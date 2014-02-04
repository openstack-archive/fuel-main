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

from glob import glob
import os
import stat


class PuppetTest:
    """This class represents single test of the Puppet module."""

    def __init__(self, test_file_path):
        """You should give this constructor path to test file."""
        self.test_file_path = test_file_path
        self.tests_path = os.path.dirname(self.test_file_path)
        self.test_file_name = os.path.basename(self.test_file_path)
        self.test_name = self.test_file_name.replace('.pp', '')
        self.find_verify_file()

    def find_verify_file(self):
        """Get verify script for this test if there is one."""
        pattern = os.path.join(self.tests_path, self.test_name) + '*'
        verify_files = glob(pattern)
        verify_files = [os.path.basename(verify_file)
                        for verify_file in verify_files
                        if not verify_file.endswith('.pp')]
        if verify_files:
            self.__verify_file = verify_files[0]
            self.make_verify_executable()
        else:
            self.__verify_file = None

    def make_verify_executable(self):
        """Set executable bit for a file."""
        file_path = os.path.join(self.tests_path, self.__verify_file)
        if not os.path.isfile(file_path):
            return False
        file_stat = os.stat(file_path)
        os.chmod(
            file_path,
            file_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return True

    @property
    def path(self):
        """Return path to test.
        Property returns path to this test relative to module and excluding
        file name
        """
        return self.tests_path

    @property
    def file(self):
        """Property returns this tests' file name."""
        return self.test_file_name

    @property
    def name(self):
        """Property returns name of this test."""
        return self.test_name

    @property
    def verify_file(self):
        """Property returns verify file name."""
        return self.__verify_file

    def __repr__(self):
        """String representation of PuppetTest."""
        return "PuppetTest(name=%s, path=%s, file=%s)" % \
               (self.name, self.path, self.file)
