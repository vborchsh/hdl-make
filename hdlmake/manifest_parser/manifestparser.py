# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
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

"""Module providing the HDLMake Manifest and its associated parser"""

from __future__ import absolute_import

from .configparser import ConfigParser


class ManifestParser(ConfigParser):

    """This is the class providing HDLMake Manifest parser capabilities"""

    def __init__(self):
        super(ManifestParser, self).__init__(
            description="Configuration options description")
        general_options = [
            {'name': 'top_module',
             'default': None,
             'help': "Top level HDL entity for synthesis and simulation, if starts with dot, then library=value of library, else lib_name.entity_name or if no dot then library is work",
             'type': ''},
            {'name': 'extra_modules',
             'default': None,
             'help': "Extra HDL entities that must be present in the design",
             'type': []},
            {'name': 'include_dirs',
             'default': None,
             'help': "Include dirs for Verilog sources",
             'type': []},
            {'name': 'action',
             'default': '',
             'help': "What is the action that should be taken if "
                      "HDLMake is run in auto mode (simulation/synthesis)",
             'type': ''},
            {'name': 'language',
             'default': 'VHDL',
             'help': "Default language to be used by the tool ",
             'type': ''},
            {'name': 'library',
             'default': None,
             'help': "Destination library for module's VHDL files",
             'type': ""},
            {'name': 'incl_makefiles',
             'default': [],
             'help': "List of .mk files appended to toplevel makefile",
             'type': []},
            {'name': 'files',
             'default': [],
             'help': "List of files from the current module",
             'type': ''},
            {'name': 'modules',
             'default': {},
             'help': "List of local modules",
             'type': {}},
            {'name': 'project_opt',
             'default': None,
             'help': 'Extra options used to create a project (Libero SoC only)',
             'type': ''}]
        self.add_option_list(general_options)
        self.add_delimiter()
        self.add_type('include_dirs', type_new="")
        self.add_type('incl_makefiles', type_new='')
        self.add_type('files', type_new=[])
        self.add_allowed_key('modules', key="svn")
        self.add_allowed_key('modules', key="git")
        self.add_allowed_key('modules', key="gitsm")
        self.add_allowed_key('modules', key="local")
        self.add_allowed_key('modules', key="system")
        fetch_options = [
            {'name': 'fetchto',
             'default': None,
             'help': "Destination for fetched modules",
             'type': ''},
            {'name': 'fetch_pre_cmd',
             'default': '',
                        'help': "Command to be executed before fetch",
                        'type': ''},
            {'name': 'fetch_post_cmd',
             'default': '',
                        'help': "Command to be executed after fetch",
                        'type': ''}]
        self.add_option_list(fetch_options)
        self.add_delimiter()
        syn_options = [
            {'name': 'syn_tool',
             'default': None,
             'help': "Tool to be used in the synthesis",
             'type': ''},
            {'name': 'syn_path',
             'default': None,
             'help': "Execution path for the Tool to be used in synthesis",
             'type': ''},
            {'name': 'syn_device',
             'default': None,
             'help': "Target FPGA device",
             'type': ''},
            {'name': 'syn_family',
             'default': None,
             'help': "Target FPGA family",
             'type': ''},
            {'name': 'syn_grade',
             'default': None,
             'help': "Speed grade of target FPGA",
             'type': ''},
            {'name': 'syn_package',
             'default': None,
             'help': "Package variant of target FPGA",
             'type': ''},
            {'name': 'syn_top',
             'default': None,
             'help': "Top level module for synthesis. Optionally prefixed with library, see top_module",
             'type': ''},
            {'name': 'syn_project',
             'default': None,
             'help': "Project file (.xise, .ise, .qpf)",
             'type': ''},
            {'name': 'syn_properties',
             'default': None,
             'help': "Synthesis properties",
             'type': []},
            {'name': 'syn_pre_project_cmd',
             'default': '',
             'help': "Command to be executed before target: project",
             'type': ''},
            {'name': 'syn_project_extra_files',
             'default': '',
             'help': "List of extra files to be sourced before saving the project (Libero SoC only)",
             'type': []},
            {'name': 'syn_post_project_cmd',
             'default': '',
             'help': "Command to be executed after target: project",
             'type': ''},
            {'name': 'syn_pre_synthesize_cmd',
             'default': '',
             'help': "Command to be executed before target: synthesize",
             'type': ''},
            {'name': 'syn_post_synthesize_cmd',
             'default': '',
             'help': "Command to be executed after target: synthesize",
             'type': ''},
            {'name': 'syn_pre_translate_cmd',
             'default': '',
             'help': "Command to be executed before target: translate",
             'type': ''},
            {'name': 'syn_post_translate_cmd',
             'default': '',
             'help': "Command to be executed after target: translate",
             'type': ''},
            {'name': 'syn_pre_map_cmd',
             'default': '',
             'help': "Command to be executed before target: map",
             'type': ''},
            {'name': 'syn_post_map_cmd',
             'default': '',
             'help': "Command to be executed after target: map",
             'type': ''},
            {'name': 'syn_pre_par_cmd',
             'default': '',
             'help': "Command to be executed before target: par",
             'type': ''},
            {'name': 'syn_post_par_cmd',
             'default': '',
             'help': "Command to be executed after target: par",
             'type': ''},
            {'name': 'syn_pre_bitstream_cmd',
             'default': '',
             'help': "Command to be executed before target: bitstream",
             'type': ''},
            {'name': 'syn_post_bitstream_cmd',
             'default': '',
             'help': "Command to be executed after target: bitstream",
             'type': ''},
            {'name': 'syn_jobs',
             'default': '2',
             'help': "Number of parallel threads to be used for synthesis (Vivado only)",
             'type': ''}]
        self.add_option_list(syn_options)
        self.add_delimiter()
        quartus_options = [
            {'name': 'quartus_preflow',
             'default': None,
             'help': "Quartus pre-flow script file",
             'type': ''},
            {'name': 'quartus_postmodule',
             'default': None,
             'help': "Quartus post-module script file",
             'type': ''},
            {'name': 'quartus_postflow',
             'default': None,
             'help': "Quartus post-flow script file",
             'type': ''}]
        self.add_option_list(quartus_options)
        self.add_delimiter()
        sim_options = [
            {'name': 'sim_top',
             'default': None,
             'help': "Top level module for simulation. Optionally prefixed with library, see top_module",
             'type': ''},
            {'name': 'sim_tool',
             'default': None,
             'help': "Simulation tool to be used (e.g. isim, vsim, iverilog)",
             'type': ''},
            {'name': 'sim_path',
             'default': None,
             'help': "Execution path for the Tool to be used in simulation",
             'type': ''},
            {'name': 'sim_pre_cmd',
             'default': None,
             'help': "Command to be executed before simulation",
             'type': ''},
            {'name': 'sim_post_cmd',
             'default': None,
             'help': "Command to be executed after simulation",
             'type': ''}]
        self.add_option_list(sim_options)
        self.add_delimiter()
        modelsim_options = [
            {'name': 'modelsim_ini_path',
             'default': None,
             'help': "Directory containing a custom Modelsim .ini file",
             'type': ''},
            {'name': 'vsim_opt',
             'default': "",
             'help': "Additional options for vsim",
             'type': ''},
            {'name': 'vcom_opt',
             'default': "",
             'help': "Additional options for vcom",
             'type': ''},
            {'name': 'vlog_opt',
             'default': "",
             'help': "Additional options for vlog",
             'type': ''},
            {'name': 'vmap_opt',
             'default': "",
             'help': "Additional options for vmap",
             'type': ''}]
        self.add_option_list(modelsim_options)
        self.add_delimiter()
        self.add_option(
            'iverilog_opt',
            default="",
            help="Additional options for IVerilog",
            type='')
        self.add_delimiter()
        self.add_option(
            'ghdl_opt',
            default="",
            help="Additional options for GHDL",
            type='')
        self.add_delimiter()
        vivado_sim_options = [
            {'name': 'xvlog_opt',
             'default': "",
             'help': "Additional options for verilog",
             'type': ''},
            {'name': 'xvhdl_opt',
             'default': "",
             'help': "Additional options for vhdl",
             'type': ''}]
        self.add_option_list(vivado_sim_options)
        self.add_delimiter()

    def add_option_list(self, option_list):
        """Add to the parser a list with the options and their keys"""
        for option in option_list:
            self.add_option(option["name"],
                            default=option["default"],
                            help=option["help"],
                            type=option["type"])

    def print_help(self):
        """Print the help for the Manifest parser object"""
        self.help()
