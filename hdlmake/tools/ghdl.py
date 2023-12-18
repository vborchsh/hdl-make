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

"""Module providing support for GHDL simulator"""

from __future__ import absolute_import
import string

from .makefilesim import MakefileSim
from ..sourcefiles.srcfile import VHDLFile


class ToolGHDL(MakefileSim):

    """Class providing the interface for GHDL simulator"""

    TOOL_INFO = {
        'name': 'GHDL',
        'id': 'ghdl',
        'windows_bin': 'ghdl',
        'linux_bin': 'ghdl'}

    STANDARD_LIBS = ['ieee', 'std']

    HDL_FILES = {VHDLFile: ''}

    CLEAN_TARGETS = {'clean': ["*.cf", "*.o", "$(TOP_MODULE)", "work"],
                     'mrproper': ["*.vcd"]}

    SIMULATOR_CONTROLS = {'vlog': None,
                          'vhdl': '$(GHDL) -a --work={work} $(GHDL_OPT) $<',
                          'compiler': '$(GHDL) -e $(GHDL_OPT) $(TOP_LIBRARY).$(TOP_MODULE)'}

    def __init__(self):
        super(ToolGHDL, self).__init__()

    def _makefile_sim_options(self):
        """Print the GHDL options to the Makefile"""
        self.writeln("GHDL := ghdl")
        ghdl_opt = self.manifest_dict.get("ghdl_opt", '')
        self.writeln("GHDL_OPT := {ghdl_opt}\n".format(ghdl_opt=ghdl_opt))

    def _makefile_sim_compilation(self):
        """Print the GDHL simulation compilation target"""
        libs = self.get_all_libs()
        self._makefile_sim_libs_variables(libs)
        self.writeln("simulation: $(VERILOG_OBJ) $(VHDL_OBJ)")
        self.writeln("\t\t" + self.SIMULATOR_CONTROLS['compiler'])
        self.writeln('\n')
        self._makefile_sim_dep_files()
