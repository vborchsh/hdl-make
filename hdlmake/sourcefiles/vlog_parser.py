#!/usr/bin/python
#
# Copyright (c) 2013 CERN
# Author: Tomasz Wlostowski
#         Adrian Fiergolski
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

# A Verilog preprocessor. Still lots of stuff to be done,
# but it's already quite useful for calculating dependencies.

"""This module provides the Verilog parser for HDLMake"""

from __future__ import print_function
from __future__ import absolute_import
import os
import re
import logging

from .new_dep_solver import DepParser
from .dep_file import DepRelation
from collections import namedtuple


class VerilogPreprocessor(object):

    """This class provides the Verilog Preprocessor"""

    # Reserved verilog preprocessor keywords. The list is certainly not full
    vpp_keywords = [
        "default_nettype",
        "define",
        "line",
        "include",
        "elsif",
        "ifdef",
        "endif",
        "else",
        "undef",
        "timescale"]

    def __init__(self):
        self.vlog_file = None
        # List of macro definitions
        self.vpp_macros = []
        self.included_files = set()
        self.macro_depth = 0

    def _search_include(self, filename, parent_dir=None):
        """Look for the 'filename' Verilog include file in the
        provided 'parent_dir'. If the directory is not provided, the method
        will search for the Verilog include in every defined Verilog
        preprocessor search directory"""
        if parent_dir is not None:
            possible_file = os.path.join(parent_dir, filename)
            if os.path.isfile(possible_file):
                return os.path.abspath(possible_file)
        for searchdir in self.vlog_file.include_dirs:
            probable_file = os.path.join(searchdir, filename)
            if os.path.isfile(probable_file):
                return os.path.abspath(probable_file)
        raise Exception("Can't find {} for {} in any of the include "
                        "directories: {}".format(filename, self.vlog_file.path,
                        ', '.join(self.vlog_file.include_dirs)))

    def _preprocess_file(self, file_content, file_name, library):
        """Preprocess the content of the Verilog file"""
        def _remove_comment(text):
            """Function that removes the comments from the Verilog code"""
            def replacer(match):
                """Funtion that replace the matching comments"""
                text = match.group(0)
                if text.startswith('/'):
                    return ""
                else:
                    return text
            pattern = re.compile(
                r'//.*?$|/\*.*?\*/|"(?:\\.|[^\\"])*"',
                re.DOTALL | re.MULTILINE)
            return re.sub(pattern, replacer, text)

        def _filter_protected_regions(text):
            '''Remove regions demarked by `pragma protect being_protected/end_protected'''
            return re.sub(r'`pragma\s+protect\s+begin_protected.*`pragma\s+protect\s+end_protected\b', '', text, flags=re.DOTALL)

        def _handle_macros(text):
            '''Process text to implement ifdef/ifndef/elsif/else/endif & define logic'''
            vpp_match = namedtuple('vpp_match', ['mtext','pptype','ppident', 'macroident','ppargs','ppdefn','incfile','substid'])
            vpp_macrodefn = namedtuple('vpp_macrodefn', ['params', 'expansion'])

            def _munge_list(flist):
                '''Take the split list & normalize into a list of string literals & seperator matches'''
                assert flist
                is_match = False # if nothing was present, split inserts an empty element
                rlist = []
                while flist:
                    if is_match:
                        assert len(flist) >= 9, "_munge_list: insufficient arguments for match object"
                        rlist.append(vpp_match(flist[0],flist[1],None if not flist[2] else flist[2].strip(),
                                               flist[3],flist[4],'' if not flist[5] else flist[5].replace('\\\n',''),flist[6],flist[7]))
                        flist = flist[9:]
                    else:
                        rlist.append(flist.pop(0))
                    is_match = not is_match
                return rlist

            def _tok_string(text):
                # Quick help on patterns:
                # (?:...)   Non-grouping version of reguler parentheses
                # (?<=...)  Matches if preceded by ...
                # Tokens: 0:full text, 1:keyword, 2:identifier, 3:define-macro, 4:define-args. 5:define-value, 6:include-file
                #         7:macro-use, 8:macro-args
                toks = re.split(r'('
                                  r'(?:`(ifn?def|elsif|else|endif|define|include)'
                                    r'('
                                      r'(?<=ifdef\b)\s+(?:\w+)'
                                      r'|(?<=ifndef\b)\s+(?:\w+)'
                                      r'|(?<=elsif\b)\s+(?:\w+)'
                                      r'|(?:(?<=define\b)\s+(\w+)(?:\(([\w\s,]*)\))?[ \t]*((?:\\\n|[^\n\r])*)$)'
                                      r'|(?<=include\b)\s+["<](.+?)[">]'
                                    r')?'
                                  r')'
                                r'|(?:`(\w+)(?:\(([\w\s,]*)\))?))', text, flags=re.MULTILINE)
                return _munge_list(toks)

            parts = _tok_string(text)

            # PP tokens
            vpp_macros = {}

            def _proc_macros_layer(parts, gmacros):
                '''Process a level of macros'''
                lbuf    = ""
                front   = parts.pop(0)
                enabled = True
                handled = False # we've handled an if condition
                lmacros = dict(gmacros)

                # we should only arrive here because either the start of a string was seen
                # or an ifdef was detected
                if isinstance(front, str):
                    lbuf = front
                elif front.pptype in ('ifdef','ifndef'):
                    enabled = front.ppident in lmacros
                    if front.pptype == 'ifndef':
                        enabled = not enabled
                    handled = enabled
                else:
                    raise Exception("verilog preprocessor: unexpected token '%s'" % front[1])

                while parts:
                    # handle further ifdefs recusively
                    front = parts.pop(0)
                    if isinstance(front, str):
                        if enabled:
                            lbuf += front
                    elif front.pptype in ('ifdef', 'ifndef'):
                        # ifdef requires a new level, reinsert element & parse next level
                        parts.insert(0, front)
                        ctext, parts, cmacros = _proc_macros_layer(parts, lmacros)
                        if enabled:
                            lbuf    += ctext
                            lmacros  = cmacros
                    elif front.pptype == 'elsif':
                        if not handled:
                            enabled = front.ppident in lmacros
                            handled = enabled
                        else: # if a clause was already selected, skip this one
                            enabled = False
                    elif front.pptype == 'else':
                        if not handled:
                            enabled = True
                            handled = True
                        else:
                            enabled = False
                    elif front.pptype == 'endif':
                        return lbuf, parts, lmacros
                    elif front.pptype == 'define':
                        if enabled:
                            if front.macroident in self.vpp_keywords:
                                raise Exception("Attempt to `define a reserved preprocessor keyword")
                            lmacros[front.macroident] = vpp_macrodefn(front.ppargs, front.ppdefn)
                            lbuf += front.mtext.replace('\\\n','')
                    elif front.pptype == "include":
                        if enabled:
                            # maybe add a check for recusion here?
                            included_file_path = self._search_include(front.incfile, os.path.dirname(file_name))
                            logging.debug("File being parsed %s (library %s) includes %s",
                                          file_name, library, included_file_path)
                            # add include file to the dependancies
                            self.included_files.add(included_file_path)
                            # tokenize the file & prepend to the current stack
                            decomment = _remove_comment(open(included_file_path, "r", errors='replace').read())
                            tokens = _tok_string(decomment)
                            parts = tokens + parts
                    elif front.pptype == 'pop_macro':
                        self.macro_depth -= 1
                        assert self.macro_depth >= 0
                    elif front.substid is not None:
                        if enabled:
                            # if not front.substid in lmacros:
                            #     raise Exception("substitute unknown identifier! (%s)" % str(front))
                            if front.substid in lmacros:
                                tokens = _tok_string(lmacros[front.substid].expansion)
                                tokens.append(vpp_match(None, 'pop_macro', front.substid, None, None, None, None, None))
                                parts = tokens + parts
                                self.macro_depth += 1
                                if self.macro_depth > 30:
                                    raise Exception("Recursion level exceeded. Nested `includes?")
                            else:
                                lbuf += front.mtext
                    else:
                        raise Exception("verilog preprocessor: unexpected token '%s' from %s" % (front[1], str(front)))

                return lbuf, parts, lmacros

            return re.sub(r'^\s*\n','', _proc_macros_layer(parts, vpp_macros)[0], flags=re.MULTILINE)

        # init dependencies
        logging.debug("preprocess file %s (of length %d) in library %s",
                      file_name, len(file_content), library)
        buf = _filter_protected_regions(_remove_comment(file_content))

        return _handle_macros(buf)

    def preprocess(self, vlog_file):
        """Assign the provided 'vlog_file' to the associated class property
        and then preprocess and return the Verilog code"""
        # assert isinstance(vlog_file, VerilogFile)
        # assert isinstance(vlog_file, DepFile)
        self.vlog_file = vlog_file
        buf = open(vlog_file.path, "r", errors='replace').read()
        return self._preprocess_file(file_content=buf,
                                     file_name=vlog_file.path,
                                     library=vlog_file.library)


class VerilogParser(DepParser):

    """Class providing the Verilog Parser functionality"""

    reserved_words = ["accept_on",
                      "alias",
                      "always",
                      "always_comb",
                      "always_ff",
                      "always_latch",
                      "assert",
                      "assign",
                      "assume",
                      "automatic",
                      "before",
                      "begin",
                      "bind",
                      "bins",
                      "binsof",
                      "bit",
                      "break",
                      "buf",
                      "bufif0",
                      "bufif1",
                      "byte",
                      "case",
                      "casex",
                      "casez",
                      "cell",
                      "chandle",
                      "checker",
                      "class",
                      "clocking",
                      "cmos",
                      "config",
                      "const",
                      "constraint",
                      "context",
                      "continue",
                      "cover",
                      "covergroup",
                      "coverpoint",
                      "cross",
                      "deassign",
                      "default",
                      "defparam",
                      "disable",
                      "dist",
                      "do",
                      "edge",
                      "else",
                      "end",
                      "endcase",
                      "endchecker",
                      "endclass",
                      "endclocking",
                      "endconfig",
                      "endfunction",
                      "endgenerate",
                      "endgroup",
                      "endinterface",
                      "endmodule",
                      "endpackage",
                      "endprimitive",
                      "endprogram",
                      "endproperty",
                      "endsequence",
                      "endspecify",
                      "endtable",
                      "endtask",
                      "enum",
                      "event",
                      "eventually",
                      "expect",
                      "export",
                      "extends",
                      "extern",
                      "final",
                      "first_match",
                      "for",
                      "force",
                      "foreach",
                      "forever",
                      "fork",
                      "forkjoin",
                      "function",
                      "generate",
                      "genvar",
                      "global",
                      "highz0",
                      "highz1",
                      "if",
                      "iff",
                      "ifnone",
                      "ignore_bins",
                      "illegal_bins",
                      "implies",
                      "import",
                      "incdir",
                      "include",
                      "initial",
                      "inout",
                      "input",
                      "inside",
                      "instance",
                      "int",
                      "integer",
                      "interface",
                      "intersect",
                      "join",
                      "join_any",
                      "join_none",
                      "large",
                      "let",
                      "liblist",
                      "library",
                      "local",
                      "localparam",
                      "logic",
                      "longint",
                      "macromodule",
                      "matches",
                      "medium",
                      "modport",
                      "module",
                      "nand",
                      "negedge",
                      "new",
                      "nexttime",
                      "nmos",
                      "nor",
                      "noshowcancelled",
                      "not",
                      "notif0",
                      "notif1",
                      "null",
                      "or",
                      "output",
                      "package",
                      "packed",
                      "parameter",
                      "pmos",
                      "posedge",
                      "primitive",
                      "priority",
                      "program",
                      "property",
                      "protected",
                      "pull0",
                      "pull1",
                      "pulldown",
                      "pullup",
                      "pulsestyle_ondetect",
                      "pulsestyle_onevent",
                      "pure",
                      "rand",
                      "randc",
                      "randcase",
                      "randsequence",
                      "rcmos",
                      "real",
                      "realtime",
                      "ref",
                      "reg",
                      "reject_on",
                      "release",
                      "repeat",
                      "restrict",
                      "return",
                      "rnmos",
                      "rpmos",
                      "rtran",
                      "rtranif0",
                      "rtranif1",
                      "s_always",
                      "scalared",
                      "sequence",
                      "s_eventually",
                      "shortint",
                      "shortreal",
                      "showcancelled",
                      "signed",
                      "small",
                      "s_nexttime",
                      "solve",
                      "specify",
                      "specparam",
                      "static",
                      "string",
                      "strong",
                      "strong0",
                      "strong1",
                      "struct",
                      "s_until",
                      "super",
                      "supply0",
                      "supply1",
                      "sync_accept_on",
                      "sync_reject_on",
                      "table",
                      "tagged",
                      "task",
                      "this",
                      "throughout",
                      "time",
                      "timeprecision",
                      "timeunit",
                      "tran",
                      "tranif0",
                      "tranif1",
                      "tri",
                      "tri0",
                      "tri1",
                      "triand",
                      "trior",
                      "trireg",
                      "type",
                      "typedef",
                      "union",
                      "unique",
                      "unique0",
                      "unsigned",
                      "until",
                      "until_with",
                      "untypted",
                      "use",
                      "var",
                      "vectored",
                      "virtual",
                      "void",
                      "wait",
                      "wait_order",
                      "wand",
                      "weak",
                      "weak0",
                      "weak1",
                      "while",
                      "wildcard",
                      "wire",
                      "with",
                      "within",
                      "wor",
                      "xnor",
                      "xor"]

    def parse(self, dep_file, graph):
        """Parse the provided Verilog file and add to its properties
        all of the detected dependency relations"""
        # assert isinstance(dep_file, DepFile), print("unexpected type: " +
        # str(type(dep_file)))

        # Preprocess the file and add included files as dependencies
        self.preprocessor = VerilogPreprocessor()
        buf = self.preprocessor.preprocess(dep_file)
        dep_file.included_files = self.preprocessor.included_files
        logging.debug("%s has %d includes.", str(dep_file), len(dep_file.included_files))

        # look for packages used inside in file
        # it may generate false dependencies as package in SV can be used by:
        #    import my_package::*;
        # or directly
        #    logic var = my_package::MY_CONST;
        # The same way constants and others can be imported directly from
        # other modules:
        #    logic var = my_other_module::MY_CONST;
        # and HdlMake will anyway create dependency marking my_other_module as
        # requested package
        import_pattern = re.compile(r"(\w+) *::(\w+|\\*)")

        def do_imports(text):
            """Function to be applied by re.subn to every match of the
            import_pattern in the Verilog code -- group() returns positive
            matches as indexed plain strings. It adds the found USE
            relations to the file"""
            pkg_name = text.group(1)
            logging.debug("file %s imports/uses %s.%s package",
                          dep_file.path, dep_file.library, pkg_name)
            graph.add_require(
                dep_file,
                DepRelation(pkg_name, dep_file.library, DepRelation.PACKAGE))
        import_pattern.subn(do_imports, buf)

        # packages
        m_inside_package = re.compile(
            r"package\s+(\w+)\s*(?:\(.*?\))?\s*(.+?)endpackage",
            re.DOTALL | re.MULTILINE)

        def do_package(text):
            """Function to be applied by re.subn to every match of the
            m_inside_pattern in the Verilog code -- group() returns positive
            matches as indexed plain strings. It adds the found PROVIDE
            relations to the file"""
            pkg_name = text.group(1)
            logging.debug("found pacakge %s.%s", dep_file.library, pkg_name)
            graph.add_provide(
                dep_file,
                DepRelation(pkg_name, dep_file.library, DepRelation.PACKAGE))
        m_inside_package.subn(do_package, buf)

        # modules and instantiations
        m_inside_module = re.compile(
            r"(?:module|interface)"
                r"\s+(?P<module_name>\w+)"
                # opt-parameters
                r"\s*(?:#\s*\(.*?\)\s*)?"
                r"(?:\((?P<port_map>.*?)\))?"
                r"\s*;\s*(?P<module_body>.*?)"
                # stmts
                r"(?:endmodule|endinterface)",
            re.DOTALL | re.MULTILINE)

        get_interface = re.compile(
            r"^\s*(?!input|output|inout)(\w+)(\.\w+)?\s+\w+",
            re.DOTALL | re.MULTILINE)

        m_instantiation = re.compile(
            r"\s*\b(\w+)\s+(?:#\s*\(.*?\)\s*)?(\w+)\s*(?:\[.*?\]\s*)?\(.*?\)$",
            re.DOTALL | re.MULTILINE)

        m_stmt = re.compile(r'(?:\s*(?:(?:\b(?:function|task)\b.*?\bend(?:function|task)\b)'
                                     r'|(?:\bbegin(?:\s*:\s*\w+)?)'
                                     r'|(?:\bend\b(?:\s*:\s*\w+)?)'
                                     r'|(?:end(?:generate|case)\b)'
                                     r'|(?:\b(?:case|if|for)\s*\(.*?\))'
                                     r'|(?:\b(?:else|generate)\b)'
                                     r'|\b(?:assign|localparam|wire|logic|reg)\b[^;]*?(?:=.*?)?;'
                                     r'|\balways(?:_ff|_latch|_comb)?\b\s*(?:@\s*(?:\*|(?:\(.*?\))))?'
                                     r'|;)\s*)+',
                            re.MULTILINE | re.DOTALL)

        def do_module(text):
            """Function to be applied by re.sub to every match of the
            m_inside_module in the Verilog code -- group() returns
            positive  matches as indexed plain strings. It adds the found
            PROVIDE relations to the file"""
            module_name = text.group("module_name")
            portmap = text.group("port_map")
            logging.debug("found module %s.%s", dep_file.library, module_name)
            graph.add_provide(
                dep_file,
                DepRelation(module_name, dep_file.library, DepRelation.MODULE))

            def do_interface(text):
                for i in get_interface.finditer(text):
                    logging.debug(f"found interface: {i.group(1)}")
                    rel = DepRelation(i.group(1), dep_file.library, DepRelation.MODULE)
                    graph.add_require(dep_file, rel)

            # if we are parsing interface we just 
            # skip the parsing of interfaces 
            if portmap:
                do_interface(portmap)

            def do_inst(text):
                """Function to be applied by re.sub to every match of the
                m_instantiation in the Verilog code -- group() returns positive
                matches as indexed plain strings. It adds the found USE
                relations to the file"""
                mod_name = text.group(1)
                if mod_name in self.reserved_words:
                    # A gate (and, or, ...)
                    return
                logging.debug("-> instantiates %s.%s as %s",
                              dep_file.library, mod_name, text.group(2))
                graph.add_require(
                    dep_file,
                    DepRelation(mod_name, dep_file.library, DepRelation.MODULE))
            for stmt in [x for x in m_stmt.split(text.group("module_body")) if x and x[-1] == ")"]:
                match = m_instantiation.match(stmt)
                if match:
                    do_inst(match)
        m_inside_module.subn(do_module, buf)

