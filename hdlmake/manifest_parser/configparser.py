# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
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

"""Module providing the parser for HDLMake Manifest.py files"""

from __future__ import print_function
from __future__ import absolute_import
import logging
import os
import sys
if sys.version[0] != "2":
    from io import StringIO
else:
    from StringIO import StringIO
import contextlib


@contextlib.contextmanager
def capture_stdout():
    """This is a function used to grab the stdout from
    the executed Manifest.py files"""
    old = sys.stdout
    sys.stdout = StringIO()
    yield sys.stdout
    sys.stdout = old


class ConfigParser(object):

    """Class for parsing python configuration files

    Case1: Normal usage
    >>> f = open("test.py", "w")
    >>> f.write('modules = {"local":"/path/to/local", "svn":"path/to/svn"}; ')
    >>> f.write('fetchto = ".."' )
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("modules", type={})
    >>> p.add_option("fetchto", type='')
    >>> p.add_config_file("test.py")
    >>> p.parse()
    {'modules': {'svn': 'path/to/svn', 'local': '/path/to/local'}, \
'fetchto': '..'}

    Case2: Default value and lack of a variable
    >>> f = open("test.py", "w")
    >>> f.write('a="123"')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("a", type='')
    >>> p.add_option("b", type='', default='borsuk')
    >>> p.add_config_file("test.py")
    >>> p.parse()
    {'a': '123', 'b': 'borsuk'}

    Case3: Multiple types for a variable
    >>> f = open("test.py", "w")
    >>> f.write('a=[1,2,3]')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("a", type=1, default=12)
    >>> p.add_type("a", type=[])
    >>> p.add_config_file("test.py")
    >>> p.parse()
    {'a': [1, 2, 3]}

    Case4: Unrecognized options
    >>> f = open("test.py", "w")
    >>> f.write('a = 123')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("b", type='')
    >>> p.add_config_file("test.py")
    >>> p.parse()
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
        File "configparser.py", line 107, in parse
        raise NameError("Unrecognized option: " + key)
    NameError: Unrecognized option: a

    Case5: Invalid parameter type
    >>> f = open("test.py","w")
    >>> f.write('a="123"')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("a", type=0)
    >>> p.add_config_file("test.py")
    >>> p.parse()
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
        File "configparser.py", line 110, in parse
        raise RuntimeError("Given option: "+str(type(val))+" doesn't match \
specified types:"+str(opt.types))
    RuntimeError: Given option: <type 'str'> doesn't match specified \
types:[<type 'int'>]

    Case6:
    >>> f = open("test.py","w")
    >>> f.write('a={"zupa":1}')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("a", type={})
    >>> p.add_allowed_key("a", "zupa")
    >>> p.add_config_file("test.py")
    >>> p.parse()
    {'a': {'zupa': 1}}

    Case7
    >>> f = open("test.py","w")
    >>> f.write('a={"kot":1}')
    >>> f.close()
    >>> p = ConfigParser()
    >>> p.add_option("a", type={})
    >>> p.add_allowed_key("a", "kniaz")
    >>> p.add_config_file("test.py")
    >>> p.parse()
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
        File "configparser.py", line 184, in parse
        raise RuntimeError("Encountered unallowed key: " +key+ " for options \
'"+opt_name+"'")
    RuntimeError: Encountered unallowed key: kot for options 'a'

    Cleanup:
    >>> import os
    >>> os.remove("test.py")
    """

    class Option(object):

        """This subclass provides instances acting as a convenient storage
        for Manifest.py options"""

        def __init__(self, name, **others):
            self.name = name
            self.keys = []
            self.types = []
            self.help = ""
            self.default = None

            for key in others:
                if key == "help":
                    self.help = others["help"]
                elif key == "default":
                    self.default = others["default"]
                elif key == "type":
                    self.add_type(type_obj=others["type"])
                else:
                    raise ValueError("Option not recognized: " + key)

        def add_type(self, type_obj):
            """Add a new supported type for the option's value"""
            self.types.append(type(type_obj))

        def add_key(self, key):
            """Add a new dict key. Note that this is only allowed when
            the option's value is a dict!!"""
            if not isinstance(key, str):
                raise ValueError("Allowed key must be a string")
            if dict not in self.types:
                raise RuntimeError(
                    "Allowing a key makes sense for dictionaries only, {}".format(self.types))
            self.keys.append(key)

    def __init__(self, description=None):
        if description is not None:
            if not isinstance(description, str):
                raise ValueError("Description should be a string!")
        self.description = description
        self.options = []
        self.prefix_code = ""
        self.suffix_code = ""
        self.config_file = None

    def __getitem__(self, name):
        if name in self.__names():
            return [x for x in self.options
                    if x is not None and x.name == name][0]
        else:
            raise RuntimeError("No such option as " + str(name))

    def help(self):
        """A method that prints the Manifest help to Host O.S. stdout"""
        print("Variables with special meaning for Hdlmake:")
        for opt in self.options:
            if opt is None:
                print("")
                continue
            print('  {0:15}; {1:29}; {2:45}, default={3:10}'.format(
                opt.name, str(opt.types), opt.help, opt.default or '""'))

    def add_option(self, name, **others):
        """Add a new Option object and add it to the parser's option list"""
        if name in self.__names():
            raise ValueError("Option already added: " + name)
        self.options.append(ConfigParser.Option(name, **others))

    def add_type(self, name, type_new):
        """Grab the specified option from parser's list and add a new type"""
        if name not in self.__names():
            raise RuntimeError("Can't add type to a non-existing option")
        self[name].add_type(type_new)

    def add_delimiter(self):
        """Append an empty element in the parser's options list"""
        self.options.append(None)

    def add_allowed_key(self, name, key):
        """Grab the specified option from parser's list and add a new dict key.
        Note that this is only allowed when the option's value is a dict!!"""
        self[name].add_key(key)

    def add_prefix_code(self, code):
        """Add the arbitrary Python to be executed just before the Manifest"""
        self.prefix_code += code + '\n'

    def add_suffix_code(self, code):
        """Add the arbitrary Python to be executed just after the Manifest"""
        self.suffix_code += code + '\n'

    def __names(self):
        """A method that returns a list containing the name for every non
        empty object in the parser's option instance list"""
        return [o.name for o in self.options if o is not None]

    def __parser_runner(self, content, extra_context):
        """method that acts as an 'exec' wraper to run the Python code.  Return the locals"""
        options = {}
        try:
            with capture_stdout() as stdout_aux:
                root_path = os.getcwd()
                exec_path = os.path.dirname(self.config_file)
                os.chdir(exec_path)
                exec(content, extra_context, options)
                os.chdir(root_path)
            printed = stdout_aux.getvalue()
            if len(printed) > 0:
                logging.info(
                    "The manifest inside {} tried to print something:".format(
                        self.config_file))
                for line in printed.split('\n'):
                    print("> " + line)
        except SyntaxError as error_syntax:
            raise Exception("Invalid syntax in the manifest file {}:\n {}{}".format(
                            self.config_file, str(error_syntax), content))
        except SystemExit as error_exit:
            raise Exception("Exit requested by the manifest file {}:\n{}{}".format(
                            self.config_file, str(error_exit), content))
        except:
            logging.error("Encountered unexpected error while parsing {}".format(
                          self.config_file))
            logging.error(content)
            print(str(sys.exc_info()[0]) + ':' + str(sys.exc_info()[1]))
            raise
        return options

    def __read_config_content(self):
        """Load the Manifest.py file content in a local variable and return
        the obtained value as a string"""
        assert self.config_file is not None
        return open(self.config_file, "r").read()

    def parse(self, config_file, extra_context=None):
        """Parse the stored manifest plus arbitrary code. Return a dictionary
        of variables defined in the manifest."""
        assert isinstance(extra_context, dict) or extra_context is None

        self.config_file = config_file

        # These HDLMake keys must not be inherited from parent module
        key_purge_list = ["modules", "files", "include_dirs",
                          "inc_makefiles", "library"]
        for key_to_be_deleted in key_purge_list:
            extra_context.pop(key_to_be_deleted, None)
        # Load the Manifest.py file content in a local variable
        content = self.__read_config_content()
        # Now, grab the options coming from Manifest.py plus arbitrary_code:
        # - extra_context as global variables.
        # - options as local variables.
        content = self.prefix_code + '\n' + content + '\n' + self.suffix_code
        options = self.__parser_runner(content, extra_context)
        # Check the options that were defined in the local context
        ret = {}
        for opt_name, val in list(options.items()):
            # Manifest variables starting with __(name) will be ignored,
            # so won't be inherited by the childrens of the module using this
            # parser.
            if opt_name.startswith('__'):
                continue
            # Only if the option is not one of the meaningful set for HDLMake,
            # create a new entry in the dictionary to be returned and pass...
            # we won't check the unknown option, but will pass it to the
            # children modules' Manifest
            if opt_name not in self.__names():
                ret[opt_name] = val
                logging.debug("New variable found: %s (=%s).", opt_name, val)
                continue
            # If we are here, is because this is a meaningful option,
            # e.g. syn_top, modules, files... grab the option instance!
            opt = self[opt_name]
            if type(val) not in opt.types:
                raise RuntimeError(
                    "Given option '%s' is of type %s: '%s', it doesn't match allowed types: (%s), file %s" %
                    (opt_name, str(type(val)), val, str(opt.types), self.config_file))
            ret[opt_name] = val
            # This is only for the options of the dictionary class:
            if isinstance(val, dict):
                for key in val:
                    if key not in self[opt_name].keys:
                        raise RuntimeError(
                            "Unallowed key: '{}' for option '{}'".format(
                                key, opt_name))

        # Set the default values for those values that were not produced
        # by the Python exec operation.
        #for opt in self.options:
        #    try:
        #        if opt.name not in ret:
        #            ret[opt.name] = opt.default
        #    except AttributeError:  # no default value in the option
        #        pass
        return ret
