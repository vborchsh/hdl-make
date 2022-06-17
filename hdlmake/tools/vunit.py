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
    if top_manifest.manifest_dict.get("vunit_language") is None:
        raise Exception("vunit_language variable must be set in the \
 top manifest, Use verilog or vhdl..")

    if top_manifest.manifest_dict.get("vunit_script") is None:
        raise Exception("vunit_script variable must be set in the \
 top manifest, Use name of VUnit simulation script.")


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

    def write_makefile(self, top_manifest, fileset, filename=None):
        """ Writes makefile exploiting VUnit simulation target"""
        _check_simulation_manifest(top_manifest)
        self.makefile_setup(top_manifest,
                            fileset,
                            filename=filename)
        self.makefile_open_write_close()

    def is_verilog_testbench(self, fl):
        """Returns True if given file has pattern of verilog or
        systemverilog testbench file. Testbench must start or end by
        _tb and has to be SV/V file"""
        if any((isinstance(fl, VerilogFile),
                isinstance(fl, SVFile))) and\
                (fl.purename.lower().startswith("tb_") or
                 fl.purename.lower().endswith("_tb")):
            return True
        return False

    def pre_build_file_set_hook(self, file_set):
        """Modifies the files to contain path for system-wide
        installed VUnit include vunit_defines.svh"""

        include_path = join(dirname(vunit.__file__), "verilog")
        vunit_include = join(include_path, "include")

        for fl in file_set:
            if self.is_verilog_testbench(fl):
                logging.debug("Modifying to include dirs of %s to include VUnit" % fl.purename)
                fl.include_dirs.append(vunit_include)
                logging.debug("INCLUDE_DIRS: %s" %
                              repr(fl.include_dirs))

        return file_set
