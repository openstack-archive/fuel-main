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

import jinja2

from puppet_module import PuppetModule


class PuppetTestGenerator:
    """Puppet Test Generator
    This is main class. It finds all modules in the given directory and creates
    tests for them.
    You should give constructor following arguments:

        - local_modules_path* Path to puppet modules which will be scanned for
        test files
        - tests_directory_path* Output directory where files will be written
        - debug level
    """

    def __init__(self, tests_directory_path, modules_path):
        """Constructor
        Constructor
        """
        if not os.path.isdir(modules_path):
            logging.error('No such directory: ' + modules_path)

        if not os.path.isdir(tests_directory_path):
            logging.error('No such directory: ' + tests_directory_path)

        self.modules_path = modules_path
        self.tests_directory = tests_directory_path

        self.default_template = 'puppet_module_test.py.tmpl'
        self.test_file_prefix = 'TestPuppetModule'

        self.modules = []
        self.module_templates = {}
        self.make_tests_dir = os.path.dirname(os.path.abspath(__file__))

        if not os.path.isdir('puppet_tests/templates'):
            logging.error("No such directory: puppet_tests/templates")
        self.template_directory = 'puppet_tests/templates'
        self.template_loader = jinja2.FileSystemLoader(
            searchpath='puppet_tests/templates')
        self.template_environment = jinja2.Environment(
            loader=self.template_loader,
        )

        self.internal_modules_path = '/etc/puppet/modules'
        self.internal_manifests_path = '/etc/puppet/manifests'

        self.find_modules()

    def find_modules(self):
        """Find modules in library path
        Find all Puppet modules in module_library_path
        and create array of PuppetModule objects
        """
        logging.debug('Starting find modules in "%s"' % self.modules_path)
        for module_dir in os.listdir(self.modules_path):
            full_module_path = os.path.join(self.modules_path, module_dir)
            full_tests_path = os.path.join(full_module_path, 'tests')
            if not os.path.isdir(full_tests_path):
                continue
            logging.debug('Found Puppet module: "%s"' % full_module_path)
            puppet_module = PuppetModule(full_module_path)
            self.modules.append(puppet_module)

    def compile_script(self, module):
        """Compile script template
        Compile script template for given module and return it
        """
        template_file = self.module_templates.get(module.name,
                                                  self.default_template)
        template = self.template_environment.get_template(template_file)
        general = {
            'local_modules_path': self.modules_path,
            'internal_modules_path': self.internal_modules_path,
            'internal_manifests_path': self.internal_manifests_path,
            'tests_directory_path': self.tests_directory
        }
        compiled_template = template.render(module=module, **general)
        return compiled_template

    def save_script(self, module):
        """Save compiled script
        Saves compiled script to a file
        """
        file_name = self.test_file_prefix + module.name.title() + '.py'
        full_file_path = os.path.join(self.tests_directory, file_name)
        script_content = self.compile_script(module)
        script_file = open(full_file_path, 'w+')
        script_file.write(script_content)
        script_file.close()

    def make_all_scripts(self):
        """Compile and save all scripts
        Compile and save to tests_directory_path all the test scripts.
        Main function.
        """
        for module in self.modules:
            logging.debug('Processing module: "%s"' % module.name)
            self.save_script(module)

    def remove_all_tests(self):
        """Remove all tests
        Remove all tests from tests_directory_path
        """
        file_list = os.listdir(self.tests_directory)
        for test_file in file_list:
            if not test_file.endswith('.py'):
                continue
            if not test_file.startswith('TestPuppetModule'):
                continue
            full_file_path = os.path.join(self.tests_directory, test_file)
            logging.debug('Removing test file: "%s"' % full_file_path)
            os.remove(full_file_path)
