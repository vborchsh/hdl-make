#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com)
#
# This file is part of Hdlmake.
#
# Hdlmake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hdlmake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hdlmake.  If not, see <http://www.gnu.org/licenses/>.
#

"""Module providing common stuff for Modelsim, Vsim and riviera like simulators"""

from __future__ import absolute_import
import os
import string

from .makefilesim import MakefileSim
from ..util import shell
from ..sourcefiles.srcfile import VerilogFile, VHDLFile, SVFile
from ..util import path as path_mod
import six


class MakefileVsim(MakefileSim):

    """A Makefile writer for simulation suitable for vsim based simulators.

    Currently used by:
      - Modelsim
      - Riviera
    """

    HDL_FILES = {VerilogFile: '', VHDLFile: '', SVFile: ''}

    def __init__(self):
        super(MakefileVsim, self).__init__()
        # These are variables that will be set in the makefile
        # The key is the variable name, and the value is the variable value
        self.custom_variables = {}
        # Additional sim dependencies (e.g. modelsim.ini)
        self.additional_deps = []
        # These are files copied into your working directory by a make rule
        # The key is the filename, the value is the file source path
        self.copy_rules = {}

    def _makefile_sim_options(self):
        """Print the vsim options to the Makefile"""
        def __get_rid_of_vsim_incdirs(vlog_opt=""):
            """Parse the VLOG options and purge the included dirs"""
            if not vlog_opt:
                vlog_opt = ""
            vlogs = vlog_opt.split(' ')
            ret = []
            for vlog_aux in vlogs:
                if not vlog_aux.startswith("+incdir+"):
                    ret.append(vlog_aux)
            return ' '.join(ret)
        vcom_flags = "-quiet " + self.manifest_dict.get("vcom_opt", '')
        vsim_flags = "" + self.manifest_dict.get("vsim_opt", '')
        vlog_flags = "-quiet " + __get_rid_of_vsim_incdirs(
            self.manifest_dict.get("vlog_opt", ''))
        vmap_flags = "" + self.manifest_dict.get("vmap_opt", '')
        for var, value in six.iteritems(self.custom_variables):
            self.writeln("%s := %s" % (var, value))
        self.writeln()
        self.writeln("VCOM_FLAGS := %s" % vcom_flags)
        self.writeln("VSIM_FLAGS := %s" % vsim_flags)
        self.writeln("VLOG_FLAGS := %s" % vlog_flags)
        self.writeln("VMAP_FLAGS := %s" % vmap_flags)

    def _makefile_sim_compile_file(self, srcfile):
        if isinstance(srcfile, VerilogFile):
            return "vlog -work {library} $(VLOG_FLAGS) {sv_option} $(INCLUDE_DIRS) $<".format(
                library=srcfile.library, sv_option="-sv" if isinstance(srcfile, SVFile) else "")
        elif isinstance(srcfile, VHDLFile):
            return "vcom $(VCOM_FLAGS) -work {} $< ".format(srcfile.library)
        else:
            return None

    def get_stamp_library_dir(self, lib):
        """Return the directory that contains the stamp files"""
        return self.objdir + lib + shell.makefile_slash_char() + "hdlmake"

    def get_stamp_library(self, lib):
        """Return the stamp file for :param lib:  It must be a proper file
        and not a directory (whose mtime is updated when a new file is created)"""
        return self.get_stamp_library_dir(lib) + shell.makefile_slash_char() + lib + "-stamp"

    def get_stamp_file(self, dep_file):
        """Stamp file for source file :param file:"""
        return self.get_stamp_library_dir(dep_file.library) + shell.makefile_slash_char() + \
            "{}_{}".format(dep_file.purename, dep_file.extension())

    def _makefile_touch_stamp_file(self):
        self.write("\t\t@" + shell.touch_command() + " $@\n")

    def _makefile_sim_libraries(self, libs):
        for lib in libs:
            stampdir = self.get_stamp_library_dir(lib)
            stamplib = self.get_stamp_library(lib)
            self.writeln("{}:".format(stamplib))
            if_objdir__objdir_lib = ''
            if self.objdir:
                if_objdir__objdir_lib = " {objdir}{lib}".format(
                    objdir=self.objdir,
                    lib=lib,
                )
            self.writeln("\t(vlib {objdir}{lib} && vmap $(VMAP_FLAGS) {lib}{if_objdir__objdir_lib} "
                         "&& {mkdir} {stampdir} && {touch} {stamplib}) || {rm} {objdir}{lib}".format(
                objdir=self.objdir,
                if_objdir__objdir_lib=if_objdir__objdir_lib,
                lib=lib, mkdir=shell.mkdir_command(), stampdir=stampdir,
                touch=shell.touch_command(), stamplib=stamplib,
                rm=shell.del_command()))
            self.writeln()

    def _makefile_sim_compilation(self):
        """Write a properly formatted Makefile for the simulator.
        The Makefile format is shared, but flags, dependencies, clean rules,
        etc are defined by the specific tool.
        """
        if self.manifest_dict.get("include_dirs") is None:
            self.writeln("INCLUDE_DIRS :=")
        else:
            self.writeln("INCLUDE_DIRS := +incdir+%s" %
                ('+'.join(self.manifest_dict.get("include_dirs"))))
        libs = self.get_all_libs()
        self._makefile_sim_libs_variables(libs)
        self.writeln(
            "simulation: {objdir}{additional_deps} $(LIB_IND) $(VERILOG_OBJ) $(VHDL_OBJ)".format(
                objdir = self.objdir + ' ' if self.objdir else '',
                additional_deps = ' '.join(self.additional_deps)
            )
        )
        self.writeln("$(VERILOG_OBJ): " + ' '.join(self.additional_deps))
        self.writeln("$(VHDL_OBJ): $(LIB_IND) " + ' '.join(self.additional_deps))
        self.writeln()
        for filename, filesource in six.iteritems(self.copy_rules):
            self.writeln("{}: {}".format(filename, filesource))
            self.writeln("\t\t{} $< . 2>&1".format(shell.copy_command()))
            self.writeln()
        self._makefile_sim_libraries(libs)
        self._makefile_sim_dep_files()
