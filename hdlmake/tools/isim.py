#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
# Modified to allow ISim simulation by Adrian Byszuk (adrian.byszuk@lnls.br)
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

"""Module providing support for Xilinx ISim simulator"""

from __future__ import absolute_import
import os
import os.path
import logging

from .makefilesim import MakefileSim
from ..util import shell
from ..sourcefiles.srcfile import VerilogFile, VHDLFile


class ToolISim(MakefileSim):

    """Class providing the interface for Xilinx ISim simulator"""

    TOOL_INFO = {
        'name': 'ISim',
        'id': 'isim',
        'windows_bin': 'isimgui.exe',
        'linux_bin': 'isimgui'}

    STANDARD_LIBS = ['std', 'ieee', 'ieee_proposed', 'vl', 'synopsys',
                     'simprim', 'unisim', 'unimacro', 'aim', 'cpld',
                     'pls', 'xilinxcorelib', 'aim_ver', 'cpld_ver',
                     'simprims_ver', 'unisims_ver', 'uni9000_ver',
                     'unimacro_ver', 'xilinxcorelib_ver', 'secureip']

    HDL_FILES = {VerilogFile: '', VHDLFile: ''}

    CLEAN_TARGETS = {'clean': ["xilinxsim.ini $(LIBS)", "fuse.xmsgs",
                               "fuse.log", "fuseRelaunch.cmd", "isim",
                               "isim.log", "isim.wdb", "isim_proj",
                               "isim_proj.*"],
                     'mrproper': ["*.vcd"]}

    def __init__(self):
        super(ToolISim, self).__init__()

    def _makefile_sim_top(self):
        """Print the top section of the Makefile for Xilinx ISim"""

        def __get_xilinxsim_ini_dir():
            """Get Xilinx ISim ini simulation file"""
            xilinx_dir = str(os.path.join(
                self.manifest_dict["sim_path"], "..", ".."))
            hdl_language = 'vhdl'  # 'verilog'
            if shell.check_windows_tools():
                os_prefix = 'nt'
            else:
                os_prefix = 'lin'
            if shell.architecture() == 32:
                arch_suffix = ''
            else:
                arch_suffix = '64'
            xilinx_ini_path = os.path.join(
                xilinx_dir, hdl_language, "hdp", os_prefix + arch_suffix)
            # Ensure the path is absolute and normalized
            return os.path.abspath(xilinx_ini_path)
        self.writeln("## variables #############################")
        self.writeln("TOP_LIBRARY := {}".format(self.get_top_library()))
        self.writeln("TOP_MODULE := {}".format(self.get_top_module()))
        self.writeln("FUSE_OUTPUT ?= isim_proj")
        self.writeln()
        self.writeln("XILINX_INI_PATH := {}".format(__get_xilinxsim_ini_dir()))
        self.writeln()

    def _makefile_sim_options(self):
        """Print the Xilinx ISim simulation options in the Makefile"""
        def __get_rid_of_isim_incdirs(vlog_opt):
            """Clean the vlog options from include dirs"""
            vlogs = vlog_opt.split(' ')
            ret = []
            skip = False
            for vlog_option in vlogs:
                if skip:
                    skip = False
                    continue
                if not vlog_option.startswith("-i"):
                    ret.append(vlog_option)
                else:
                    skip = True
            return ' '.join(ret)
        default_options = ("-intstyle default -incremental " +
                           "-initfile xilinxsim.ini ")
        self.writeln("VHPCOMP_FLAGS := " +
            default_options + self.manifest_dict.get("vcom_opt", ''))
        self.writeln("VLOGCOMP_FLAGS := " +
            default_options + __get_rid_of_isim_incdirs(
            self.manifest_dict.get("vlog_opt", '')))

    def _makefile_syn_file_rule(self, file_aux):
        """Generate target and prerequisites for :param file_aux:"""
        self.write("{}: {} ".format(self.get_stamp_file(file_aux), file_aux.rel_path()))
        self.writeln(' '.join([fname.rel_path() for fname in file_aux.depends_on]))

    def _makefile_sim_compile_file(self, srcfile):
        if isinstance(srcfile, VerilogFile):
            res = "vlogcomp -work {lib}=.{slash}{lib} $(VLOGCOMP_FLAGS) ".format(
                lib=srcfile.library, slash=shell.makefile_slash_char())
            if srcfile.include_dirs:
                res += ' -i '
                res += ' '.join(srcfile.include_dirs)
            res += " $<"
            return res
        elif isinstance(srcfile, VHDLFile):
            return "vhpcomp $(VHPCOMP_FLAGS) -work {lib}=.{slash}{lib} $< ".format(
                lib=srcfile.library, slash=shell.makefile_slash_char())
        else:
            return None

    def _makefile_sim_libraries(self, libs):
        # ISim does not have a vmap command to insert additional libraries in
        #.ini file.
        for lib in libs:
            libfile = self.get_stamp_library(lib)
            self.writeln("{}:".format(libfile))
            self.write("\t({mkdir} {lib} && {touch} {libfile}".format(
                lib=lib, libfile=libfile, mkdir=shell.mkdir_command(), touch=shell.touch_command()))
            # Modify xilinxsim.ini file by including the extra local libraries
            self.write(" && echo {lib}={lib}  >> xilinxsim.ini) ".format(lib=lib))
            self.write("|| {rm} {lib} \n".format(lib=lib, rm=shell.del_command()))
            self.writeln()

    def _makefile_sim_compilation(self):
        """Print the compile simulation target for Xilinx ISim"""
        libs = self.get_all_libs()
        self._makefile_sim_libs_variables(libs)
        self.writeln("""\
simulation: xilinxsim.ini $(LIB_IND) $(VERILOG_OBJ) $(VHDL_OBJ) fuse
$(VERILOG_OBJ): $(LIB_IND) xilinxsim.ini
$(VHDL_OBJ): $(LIB_IND) xilinxsim.ini

""")
        self.writeln("xilinxsim.ini: $(XILINX_INI_PATH)" +
            shell.makefile_slash_char() + "xilinxsim.ini")
        self.writeln("\t\t" + shell.copy_command() + " $< .")
        self.writeln("""\
fuse:
\t\tfuse $(TOP_LIBRARY).$(TOP_MODULE) -intstyle ise -incremental -o $(FUSE_OUTPUT)

""")
        self._makefile_sim_libraries(libs)
        self._makefile_sim_dep_files()
