#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import os
import re
import sys

from puppet_test import PuppetTest

path = os.path.abspath(__file__)
path = os.path.dirname(path)
sys.path.insert(0, path)


class PuppetModule:
    """This class represents Puppet module."""

    def __init__(self, local_module_path):
        """You should give this constructor the full path to the module."""
        self.local_module_path = local_module_path
        self.module_name = os.path.basename(self.local_module_path)

        self.__tests = []
        self.__dependencies = []

        self.comment_regexp = re.compile(r'^\s*#')
        self.dependency_regexp = \
            re.compile(r'^\s*dependency\s*[\'\"]*([^\'\"]+)[\'\"]*')

        self.find_tests()
        self.find_dependencies()

    def find_dependencies(self):
        """Get dependencies of this module from Modulefile if present."""
        module_file = 'Modulefile'
        dependencies = []
        module_file_path = os.path.join(self.local_module_path, module_file)
        if not os.path.isfile(module_file_path):
            self.__dependencies = dependencies
            return False
        opened_file = open(module_file_path, 'r')
        for line in opened_file.readlines():
            if re.match(self.comment_regexp, line):
                # skip commented line
                continue
            match = re.match(self.dependency_regexp, line)
            if match:
                # found dependency line
                dependency_name = match.group(1).split('/')[-1]
                dependencies.append(dependency_name)
        self.__dependencies = dependencies
        return True

    def find_tests(self):
        """Find all tests.
        Find all tests in this module and fill tests array
        with PuppetTest objects.
        """
        current_path = os.path.abspath(os.curdir)
        try:
            os.chdir(self.local_module_path)
        except OSError as error:
            logging.error("Cannot change directory to %s: %s" %
                          (self.local_module_path, error.message))
        else:
            for root, dirs, files in os.walk('tests'):
                for test_file in files:
                    if not test_file[-3:] == '.pp':
                        continue
                    test_file_path = os.path.join(root, test_file)
                    puppet_test = PuppetTest(test_file_path)
                    self.__tests.append(puppet_test)
        finally:
            # try to restore original folder on exit
            try:
                os.chdir(current_path)
            except OSError as error:
                logging.error("Cannot change directory to %s: %s" %
                              (self.local_module_path, error.message), 1)

    @property
    def tests(self):
        """Property returns list of tests."""
        return self.__tests

    @property
    def name(self):
        """Property returns module name."""
        return self.module_name

    @property
    def path(self):
        """Property returns path to this module."""
        return self.local_module_path

    @property
    def dependencies(self):
        """Property returns list of module dependencies."""
        return self.__dependencies

    def __repr__(self):
        """String representation of PuppetModule."""
        tests_string = ''
        if len(self.tests) > 0:
            tests = [repr(test) for test in self.tests]
            tests_string += ", ".join(tests)
        tpl = "PuppetModule(name=%s, path=%s, tests=[%s]" \
              % (self.name, self.path, tests_string)

        return tpl
