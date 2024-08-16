#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
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

"""Module providing the core functionality for writing Makefiles"""

from __future__ import absolute_import
import os
import logging
import re
import six

from subprocess import CalledProcessError

from ..util import shell
from ..util import path as path_mod


class ToolMakefile(object):

    """Class that provides the Makefile writing methods and status"""

    HDL_FILES = {}
    TOOL_INFO = {}
    STANDARD_LIBS = []
    SYSTEM_LIBS = []
    CLEAN_TARGETS = {}
    SUPPORTED_FILES = {}

    def __init__(self):
        super(ToolMakefile, self).__init__()
        self.objdir = self.get_obj_dir()
        # Makefile objdir variants
        self.objdir_mk = '$(PROJ_OBJ)' if self.objdir else ''
        self.objdir_mk_spc = self.objdir_mk + ' ' if self.objdir else ''
        self._filestring = ""
        self._file = None
        self.fileset = None
        self.manifest_dict = {}
        self._filename = "Makefile"
        self._all_sources = []
        self.default_library = "work"

    def __del__(self):
        if self._file:
            self._file.close()

    def get_standard_libs(self):
        """Get the standard vhdl libraries supported by the tool.  Any package
        from these libraries are considered as satisfied"""
        return self.STANDARD_LIBS

    def get_system_libs(self):
        """Get the system libs supported by the tool.  Any package or entities
        provided by those are considered as satisfied"""
        return self.SYSTEM_LIBS

    def get_parseable_files(self):
        """Get the parseable HDL file types supported by the tool"""
        return self.HDL_FILES

    def get_privative_files(self):
        """Get the privative format file types supported by the tool"""
        return self.SUPPORTED_FILES

    def get_project_root(self):
        """Get/Guess project root
        If dir is a git repo find the root of the git repo, of root module - not of otional submodule
        """
        # Try to get git toplevel and return
        # Alternative method:
        #   Use "git git rev-parse --show-cdup", which returns ../../../.. (uses slashes on both windows and linux)
        #   Thren count number of slashes just as for svn
        try:
            command_out = shell.run_popen("git rev-parse --show-toplevel")
            top_level = command_out.stdout.readlines()[0].strip().decode('utf-8')
            return top_level.replace('/', shell.makefile_slash_char())
        except CalledProcessError as process_error:
            logging.debug("Can't find git toplevel. Cannot execute the shell command: %s",
                process_error.output)
        except IndexError:
            logging.debug("Can't find git toplevel. Not a git repo.")

        # Get cwd used for both svn(to get toplevel dir) and fallback
        cwd = os.getcwd()

        # Try to get git toplevel and return
        try:
            command_out = shell.run_popen("svn info")
            svn_info_lines = [_.strip().decode('utf-8') for _ in command_out.stdout.readlines()]
            idx = [_ for _, s in enumerate(svn_info_lines) if 'Relative URL:' in s][0]
            svn_relative_url = svn_info_lines[idx]
            levels_up = svn_relative_url.count('/') - 1
            top_level = '/'.join(cwd.split(shell.makefile_slash_char())[0:-levels_up])
            return top_level.replace('/', shell.makefile_slash_char())
        except CalledProcessError as process_error:
            logging.debug("Can't find svn toplevel. Cannot execute the shell command: %s",
                process_error.output)
        except IndexError:
            logging.debug("Can't find svn toplevel. Not a svn repo.")

        # Fall back return current dir as toplevel
        return cwd

    def get_obj_dir(self):
        """Return the directory that contains the obj files"""
        objdir = os.environ.get('OBJ', '')
        if not objdir:
            return ''
        objdir = objdir.replace('/', shell.makefile_slash_char())
        objdir = objdir.replace(' ', '__')
        # If objdir find root of project and append that to objdir
        # Let objdir end with / or \ depending on OS with final '' argument.
        project_root = self.get_project_root()
        # Skip root / (for linux etc.) of project_root
        project_root = project_root.lstrip('/')
        _project_root = project_root
        if shell.check_windows_commands():
            # Colon not allowed in path except <drive>:, remove it
            _project_root = _project_root.replace(':', '')
            # If project_root is a windows network drive, then
            # it starts with '\\<share>\, remove all initial \
            _project_root = re.sub(r'\\\\+', '', _project_root)
        res = os.path.join(
            objdir,
            _project_root,
            self.TOOL_INFO.get('id', 'tool_without_id'),
        )
        return res

    def makefile_objdir_concat(self, path=None):
        """Return paths to makefile, prefix with objdir if set,
        if objdir or path includes spaces, quote the concatenated string
        path can either be None, str or list, if list each element is joined with / or \ depending on OS"""
        if path is None:
            return self.objdir_mk

        # _path = path if string or joined path if list
        p = shell.makefile_slash_char()
        _path = path
        if not _path:
            _path = ''
        if isinstance(path, list):
            _path = p.join(path)

        if self.objdir:
            return p.join([self.objdir_mk, _path])
        # path set, objdir not
        return _path


    def makefile_setup(self, top_manifest, fileset, filename=None):
        """Set the Makefile configuration"""
        self.manifest_dict = top_manifest.manifest_dict
        self.fileset = fileset
        if filename:
            self._filename = filename
        self._makefile_open()

    def _makefile_open(self):
        """Open the Makefile file and print a header"""
        if os.path.exists(self._filename):
            os.remove(self._filename)

        self.writeln("########################################")
        self.writeln("#  This file was generated by hdlmake  #")
        self.writeln("#  http://ohwr.org/projects/hdl-make/  #")
        self.writeln("########################################")
        self.writeln()
        if self.objdir:
            self.writeln("PROJ_OBJ := {objdir}".format(
                         objdir=self.objdir,
                         ))
            self.writeln()

    def _get_path(self):
        """Get the directory in which the tool binary is at Host"""
        bin_name = self.get_tool_bin()
        locations = shell.which(bin_name)
        if len(locations) == 0:
            return None
        logging.debug("location for %s: %s", bin_name, locations[0])
        return os.path.dirname(locations[0])

    def _is_in_path(self, path_key):
        """Check if the directory is in the system path"""
        path = self.manifest_dict.get(path_key)
        bin_name = self.get_tool_bin()
        return os.path.exists(os.path.join(path, bin_name))

    def _check_in_system_path(self):
        """Check if if in the system path exists a file named (name)"""
        return self._get_path() is not None

    def get_tool_bin(self):
        if shell.check_windows_tools():
            return self.TOOL_INFO["windows_bin"]
        else:
            return self.TOOL_INFO["linux_bin"]

    def makefile_check_tool(self, path_key):
        """Check if the binary is available in the O.S. environment"""
        name = self.TOOL_INFO['name']
        logging.debug("Checking if " + name + " tool is available on PATH")
        if path_key in self.manifest_dict:
            if self._is_in_path(path_key):
                logging.info("%s found under HDLMAKE_%s: %s",
                             name, path_key.upper(),
                             self.manifest_dict[path_key])
            else:
                logging.warning("%s NOT found under HDLMAKE_%s: %s",
                                name, path_key.upper(),
                                self.manifest_dict[path_key])
                self.manifest_dict[path_key] = ''
        else:
            if self._check_in_system_path():
                self.manifest_dict[path_key] = self._get_path()
                logging.info("%s found in system PATH: %s",
                             name, self.manifest_dict[path_key])
            else:
                logging.warning("%s cannnot be found in system PATH", name)
                self.manifest_dict[path_key] = ''

    def makefile_includes(self):
        """Add the included makefiles that need to be previously loaded"""
        if self.manifest_dict.get("incl_makefiles") is not None:
            for file_aux in self.manifest_dict["incl_makefiles"]:
                if os.path.exists(file_aux):
                    self.writeln("include %s" % file_aux)
                else:
                    logging.warning("Included Makefile %s NOT found.", file_aux)
            self.writeln()

    def makefile_clean(self):
        """Print the Makefile target for cleaning intermediate files"""
        clean_targets_libs = "$(LIBS)"
        if self.objdir:
            clean_targets_libs = "$(addprefix {objdir},$(LIBS))".format(objdir=self.makefile_objdir_concat(''))
        self.writeln("CLEAN_TARGETS := {clean_targets_libs} ".format(
            clean_targets_libs=clean_targets_libs) +
            ' '.join(self.CLEAN_TARGETS["clean"]) + "\n")
        self.writeln("clean:")
        self.writeln("\t\t" + shell.del_command() + " $(CLEAN_TARGETS)")
        if shell.check_windows_commands():
            tmp = "\t\t@-" + shell.rmdir_command() + \
            " $(CLEAN_TARGETS) >nul 2>&1"
            self.writeln(tmp)

    def makefile_mrproper(self):
        """Print the Makefile target for cleaning final files"""
        self.writeln("mrproper: clean")
        tmp = "\t\t" + shell.del_command() + \
            " " + ' '.join(self.CLEAN_TARGETS["mrproper"]) + "\n"
        self.writeln(tmp)

    def makefile_open_write_close(self):
        with open(self._filename, "w") as mf:
            mf.write(self._filestring)
        self._file = None

    def write(self, line=None):
        """Write a string in the manifest, no new line"""
        l = line
        if shell.check_windows_commands():
            # Change escaping of '&'.
            l = l.replace("'&'", "^&")
            # Need to remove quotes as they are needed only for unix shell.
            l = l.replace('\\"', '"')
            l = l.replace("'", "")
        self._filestring += l

    def writeln(self, text=None):
        """Write a string in the manifest, automatically add new line"""
        if text is None:
            self.write("\n")
        else:
            self.write(text + "\n")

    def get_num_hdl_libs(self):
       num_libs = len(self.get_all_libs());
       return num_libs;

    def get_library_for_top_module(self):
       if self.get_num_hdl_libs() == 1:
         # this may now be excessive, based on the "catch-all" return statement at the bottom.
         return self.default_library
       else:
         #find and return the library name for the top HDL module...
         fileset_dict = {}
         fileset_dict.update(self.HDL_FILES)
         top_file = self.manifest_dict[self.ACTION_SHORTNAME + "_top"]
         for hdlfiletype in fileset_dict:
           for specific_file in self.fileset:
             if isinstance(specific_file, hdlfiletype):
               if specific_file.purename == top_file:
                 #logging.info(self.TOOL_INFO['name']
                 #      + "libfinder_top_module, FOUND library_name: "
                 #      + specific_file.library + " for module: "
                 #      + top_file )
                 return str(specific_file.library)

       #In case we dont find a library then post an info message before returning the default value
       logging.info(  self.TOOL_INFO['name']
                    + "function get_library_for_top_module, "
                    + "failed to find a library for the top module: "
                    + top_file + " Will use the default_library: "
                    + self.default_library
                   )
       return self.default_library

    def get_top_library(self):
        ''' get_top_library
        '''
        top_library = self.manifest_dict.get(self.ACTION_SHORTNAME + "_top_library", None)
        if top_library == '?':
            top_library = self.get_library_for_top_module()
        if not top_library:
            top_library = self.default_library
        return top_library

    def get_top_module(self):
        ''' get_top_module
        '''
        return self.manifest_dict.get(self.ACTION_SHORTNAME + "_top", None)
