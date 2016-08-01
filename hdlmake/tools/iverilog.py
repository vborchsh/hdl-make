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

from subprocess import Popen, PIPE
import string
import os
import platform
import logging

from hdlmake.action import ActionMakefile


IVERILOG_STANDARD_LIBS = ['std', 'ieee', 'ieee_proposed', 'vl', 'synopsys',
                          'simprim', 'unisim', 'unimacro', 'aim', 'cpld',
                          'pls', 'xilinxcorelib', 'aim_ver', 'cpld_ver',
                          'simprims_ver', 'unisims_ver', 'uni9000_ver',
                          'unimacro_ver', 'xilinxcorelib_ver', 'secureip']


class ToolIVerilog(ActionMakefile):

    def __init__(self):
        super(ToolIVerilog, self).__init__()

    def get_keys(self):
        tool_info = {
            'name': 'Icarus Verilog',
            'id': 'iverilog',
            'windows_bin': 'iverilog',
            'linux_bin': 'iverilog'
        }
        return tool_info

    def get_standard_libraries(self):
        return IVERILOG_STANDARD_LIBS

    def detect_version(self, path):
        if platform.system() == 'Windows':
            is_windows = True
        else:
            is_windows = False
        iverilog = Popen("iverilog -v 2>/dev/null| awk '{if(NR==1) print $4}'",
                         shell=True,
                         stdin=PIPE,
                         stdout=PIPE,
                         close_fds=not is_windows)
        version = iverilog.stdout.readlines()[0].strip()
        return version

    def supported_files(self, fileset):
        from hdlmake.srcfile import SourceFileSet
        sup_files = SourceFileSet()
        return sup_files

    def generate_simulation_makefile(self, fileset, top_module):
        # TODO FLAGS: 2009 enables SystemVerilog (ongoing support) and partial
        # VHDL support

        from hdlmake.srcfile import VerilogFile, VHDLFile, SVFile

        makefile_tmplt_1 = string.Template("""TOP_MODULE := ${top_module}
IVERILOG_CRAP := \
run.command \
ivl_vhdl_work

#target for performing local simulation
local: sim_pre_cmd simulation sim_post_cmd

simulation:
""")

        makefile_text_1 = makefile_tmplt_1.substitute(
            top_module=top_module.manifest_dict["sim_top"]
        )
        self.write(makefile_text_1)

        self.writeln(
            "\t\techo \"# IVerilog command file, generated by HDLMake\" > run.command")

        for inc in top_module.get_include_dirs_list():
            self.writeln("\t\techo \"+incdir+" + inc + "\" >> run.command")

        for vl in fileset.filter(VerilogFile):
            self.writeln("\t\techo \"" + vl.rel_path() + "\" >> run.command")

        for vhdl in fileset.filter(VHDLFile):
            self.writeln("\t\techo \"" + vhdl.rel_path() + "\" >> run.command")

        for sv in fileset.filter(SVFile):
            self.writeln("\t\techo \"" + sv.rel_path() + "\" >> run.command")

        makefile_tmplt_2 = string.Template("""
\t\tiverilog ${iverilog_opt} -s $$(TOP_MODULE) -o $$(TOP_MODULE).vvp -c run.command

sim_pre_cmd:
\t\t${sim_pre_cmd}

sim_post_cmd:
\t\t${sim_post_cmd}

#target for cleaning all intermediate stuff
clean:
\t\trm -rf $$(IVERILOG_CRAP)

#target for cleaning final files
mrproper: clean
\t\trm -f *.vcd *.vvp

.PHONY: mrproper clean sim_pre_cmd sim_post_cmd simulation

""")
        if top_module.manifest_dict["iverilog_opt"]:
            iverilog_opt = top_module.manifest_dict["iverilog_opt"]
        else:
            iverilog_opt = ''

        if top_module.manifest_dict["sim_pre_cmd"]:
            sim_pre_cmd = top_module.manifest_dict["sim_pre_cmd"]
        else:
            sim_pre_cmd = ''

        if top_module.manifest_dict["sim_post_cmd"]:
            sim_post_cmd = top_module.manifest_dict["sim_post_cmd"]
        else:
            sim_post_cmd = ''

        makefile_text_2 = makefile_tmplt_2.substitute(
            iverilog_opt=iverilog_opt,
            sim_pre_cmd=sim_pre_cmd,
            sim_post_cmd=sim_post_cmd,
        )
        self.write(makefile_text_2)
