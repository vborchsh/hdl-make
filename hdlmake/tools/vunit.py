#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 CERN
# Author: David Belohrad (david.belohrad@cern.ch)
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

"""Module providing support for VUnit simulation"""

from __future__ import print_function
from __future__ import absolute_import

import logging
import vunit
from os.path import join, dirname

from .makefilesim import MakefileSim
from ..sourcefiles.srcfile import VerilogFile, VHDLFile, SVFile


def _check_simulation_manifest(top_manifest):
    """Check if the simulation keys are provided by the top manifest"""
    if top_manifest.manifest_dict.get("vunit_script") is None:
        raise Exception("vunit_script variable must be set in the \
 top manifest, Use name of VUnit simulation script.")

    if top_manifest.manifest_dict.get("tool") is None:
        raise Exception("tool variable must be set in the \
 top manifest to reflect which simulator VUnit uses. Supported values:\
 modelsim, mentor_vhdl_only, questasim, vcs, vcsmx, ncsim,\
 activehdl, rivierapro")

    if top_manifest.manifest_dict.get("target") is None:
        raise Exception("target variable must be set in the \
 top manifest. Set to altera, xilinx")

    if top_manifest.manifest_dict.get("syn_family") is None:
        raise Exception("syn_family variable must be set in the \
 top manifest. Set to Arria V, Cyclone V ...")


class ToolVunitSim(MakefileSim):

    """Class providing the interface for VUnit unit test framework"""

    TOOL_INFO = {'name': 'VUnit',
                 'id': 'vunit'}

    CLEAN_TARGETS = {'clean': ["vunit_out", "work"],
                     'mrproper': []}

    STANDARD_LIBS = ['std', 'vunit_pkg']

    HDL_FILES = {VerilogFile: '',
                 VHDLFile: '',
                 SVFile: ''}


    def __init__(self):
        super(ToolVunitSim, self).__init__()

        # VUnit does not require top-level testbench because it parses
        # all the testbenches in the given verification
        # directories. Following will dismiss warnings
        self.requires_top_level = False
        # following is dictionary of command functions which write
        # portions of makefile responsible for generation of standard
        # simulation libraries into ./sim_libs
        self.STD_LIBS_COMPILER_COMMAND =\
            {"altera": self.get_altera_compilation_script}

    def get_altera_compilation_script(self, top_manifest):
        """ produces makefile lines reponsible to generate
        sim_libs. sim_libs are generated for both VHDL and
        Verilog. Reason being that whem mixed designs are involved
        they both have to be compiled in altera because basic
        libraries have different way of configuration when VHDL and
        verilog is used """

        # according to quartus_sh the family name is all lowercase
        # stripped of spaces
        converted_name = top_manifest.manifest_dict.get('syn_family').\
            lower().replace(' ', '').strip()

        self.writeln("""$(STD_LIBS):
\t@rm -rf ${STD_LIBS}
\t@mkdir ${STD_LIBS}
\t@quartus_sh --simlib_comp -tool %s -language verilog -family %s -directory ${STD_LIBS}
\t@quartus_sh --simlib_comp -tool %s -language vhdl -family %s -directory ${STD_LIBS}
""" % (top_manifest.manifest_dict.get('tool'),
       converted_name,
       top_manifest.manifest_dict.get('tool'),
       converted_name))
        self.writeln()

    def write_makefile(self, top_manifest, fileset, filename=None):
        """ Writes makefile exploiting VUnit simulation target"""
        _check_simulation_manifest(top_manifest)
        self.makefile_setup(top_manifest,
                            fileset,
                            filename=filename)
        # we don't check VUnit here, we know it exists as it is
        # installed with this package and already loaded -> no issue.
        self._makefile_sim_vunit(top_manifest)
        self._makefile_compile_libs_vunit(top_manifest)
        self._makefile_sim_clean_vunit()
        self.makefile_open_write_close()

    def _makefile_compile_libs_vunit(self, top_manifest):
        """Inserts into makefile line to compile the altera/xilinx
        libraries"""

        try:
            self.STD_LIBS_COMPILER_COMMAND[top_manifest.manifest_dict.
                                           get('target')](top_manifest)

        except KeyError:
            self.writeln("""$(STD_LIBS):
\t@echo 'Libraries compilation as set per top-level Manifest.py not supported'
\t@echo 'Consider writing another front-end into vunit.py of hdlmake'
""")
        self.writeln()

    def _makefile_sim_vunit(self, top_manifest):
        """Writes down the core part of the makefile"""
        self.writeln("SIM_SCRIPT := {}".format(
            join(".", top_manifest.manifest_dict["vunit_script"])))
        self.writeln("STD_LIBS := ./sim_libs")
        self.writeln("""

all: | $(STD_LIBS)
\t@${SIM_SCRIPT}

compile: mrproper $(STD_LIBS)
\t@${SIM_SCRIPT} --clean --compile

""")
        self.writeln()

    def _makefile_sim_clean_vunit(self):
        """ Cleaning """
        self.writeln("""
clean:
\t@rm -rf ./vunit_out
\t@rm -rf ./work
\t@rm -rf ./modelsim.ini

mrproper: clean
\t@rm -rf ./sim_libs
""");
        self.writeln()

    def is_verilog(self, fl):
        """Returns True if given file has pattern of verilog or
        systemverilog file."""
        if any((isinstance(fl, VerilogFile),
                isinstance(fl, SVFile))):
            return True
        return False

    def pre_build_file_set_hook(self, file_set):
        """Modifies the files to contain path for system-wide
        installed VUnit include vunit_defines.svh"""

        include_path = join(dirname(vunit.__file__), "verilog")
        vunit_include = join(include_path, "include")

        if file_set is not None:
            for fl in file_set:
                if self.is_verilog(fl):
                    logging.debug("Modifying to include dirs of %s to include VUnit" % fl.purename)
                    fl.include_dirs.append(vunit_include)
                    logging.debug("INCLUDE_DIRS: %s" %
                                  repr(fl.include_dirs))

        return file_set
