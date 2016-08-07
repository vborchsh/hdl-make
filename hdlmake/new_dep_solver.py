#!/usr/bin/python
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

"""This package provides the functions and classes to parse and solve
 HDLMake filesets"""

from __future__ import print_function
import logging

from .dep_file import DepFile
from .srcfile import VHDLFile, VerilogFile, SVFile


class DepParser(object):

    """Base Class for the different HDL parsers (VHDL and Verilog)"""

    def __init__(self, dep_file):
        self.dep_file = dep_file

    def parse(self, dep_file):
        """Base dummy interface method for the HDL parse execution"""
        raise

def solve(fileset):
    """Function that Parses and Solves the provided HDL fileset. Note
       that it doesn't return a new fileset, but modifies the original one"""
    from .srcfile import SourceFileSet
    from .dep_file import DepRelation
    assert isinstance(fileset, SourceFileSet)
    fset = fileset.filter(DepFile)
    # print(fileset)
    # print(fset)
    not_satisfied = 0
    logging.debug("PARSE BEGIN: Here, we will parse all the files in the "
                  "fileset: no parsing should be done beyond this point")
    for investigated_file in fset:
        logging.debug("INVESTIGATED FILE: %s", investigated_file)
        investigated_file.parse_if_needed()
    logging.debug("PARSE END: now the parsing is done")
    logging.debug("SOLVE BEGIN")
    for investigated_file in fset:
        # logging.info("INVESTIGATED FILE: %s" % investigated_file)
        # print(investigated_file.rels)
        for rel in investigated_file.rels:
            # logging.info("- relation: %s" % rel)
            # logging.info("- direction: %s" % rel.direction)
            # Only analyze USE relations, we are looking for dependencies
            if rel.direction == DepRelation.USE:
                satisfied_by = set()
                for dep_file in fset:
                    if dep_file.satisfies(rel):
                        if dep_file is not investigated_file:
                            investigated_file.depends_on.add(dep_file)
                        satisfied_by.add(dep_file)
                if len(satisfied_by) > 1:
                    logging.warning(
                        "Relation %s satisfied by multpiple (%d) files: %s",
                        str(rel),
                        len(satisfied_by),
                        '\n'.join([file_aux.path for
                                   file_aux in list(satisfied_by)]))
                elif len(satisfied_by) == 0:
                    logging.warning(
                        "Relation %s in %s not satisfied by any source file",
                        str(rel), investigated_file.name)
                    not_satisfied += 1
    logging.debug("SOLVE END")
    if not_satisfied != 0:
        logging.warning(
            "Dependencies solved, but %d relations were not satisfied",
            not_satisfied)
    else:
        logging.info(
            "Dependencies solved, all of the relations weres satisfied!")


def make_dependency_sorted_list(fileset, reverse=False):
    """Sort files in order of dependency.
    Files with no dependencies first.
    All files that another depends on will be earlier in the list."""
    dependable = [f for f in fileset if isinstance(f, DepFile)]
    non_dependable = [f for f in fileset if not isinstance(f, DepFile)]
    dependable.sort(key=lambda f: f.file_path.lower())
                    # Not necessary, but will tend to group files more nicely
                    # in the output.
    dependable.sort(key=DepFile.get_dep_level)
    sorted_list = non_dependable + dependable
    if reverse:
        sorted_list = list(reversed(sorted_list))
    return sorted_list


def make_dependency_set(fileset, top_level_entity):
    """Create the set of all files required to build the named
     top_level_entity."""
    from hdlmake.srcfile import SourceFileSet
    from hdlmake.dep_file import DepRelation
    assert isinstance(fileset, SourceFileSet)
    fset = fileset.filter(DepFile)
    # Find the file that provides the named top level entity
    top_rel_vhdl = DepRelation(
        "%s.%s" %
        ("work", top_level_entity), DepRelation.PROVIDE, DepRelation.ENTITY)
    top_rel_vlog = DepRelation(
        "%s.%s" %
        ("work", top_level_entity), DepRelation.PROVIDE, DepRelation.MODULE)
    top_file = None
    for chk_file in fset:
        for rel in chk_file.rels:
            if (rel == top_rel_vhdl) or (rel == top_rel_vlog):
                top_file = chk_file
                break
        if top_file:
            break
    if top_file is None:
        logging.critical('Could not find a top level file that provides the '
                         'top_module="%s". Continuing with the full file set.',
                         top_level_entity)
        return fileset
    # Collect only the files that the top level entity is dependant on, by
    # walking the dependancy tree.
    try:
        dep_file_set = set()
        file_set = set([top_file])
        while True:
            chk_file = file_set.pop()
            dep_file_set.add(chk_file)
            file_set.update(chk_file.depends_on - dep_file_set)
    except KeyError:
        # no files left
        pass
    logging.info("Found %d files as dependancies of %s.",
                 len(dep_file_set), top_level_entity)
    # for dep_file in dep_file_set:
    #    logging.info("\t" + str(dep_file))
    return dep_file_set
