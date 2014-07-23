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

from fuelweb_test.helpers.decorators import debug
from fuelweb_test.helpers.decorators import upload_manifests
from fuelweb_test.models.pp_environment import PuppetEnvironment

import logging
import unittest

logger = logging.getLogger('integration')
logwrap = debug(logger)


class TestPuppetModule{{ module.name|title }}(unittest.TestCase):  # flake8: noqa
    @upload_manifests
    def setUp(self):
        self.env = PuppetEnvironment()
        self.env.await()
        self.puppet_apply = "puppet apply " \
                            "--verbose " \
                            "--detailed-exitcodes " \
                            "--modulepath='{{ internal_modules_path }}'"

        if not self.env.get_virtual_environment().has_snapshot("before_test"):
            self.env.make_snapshot(snapshot_name="before_test")
{% for test in module.tests %}  # flake8: noqa
    def test_{{ test.name|title }}(self):  # flake8: noqa
        manifest = \
            "{{ internal_modules_path }}/{{ module.name }}/{{ test.path }}/{{test.file }}"  # flake8: noqa
        result = self.env.execute_cmd("%s '%s'" % (self.puppet_apply,manifest))  # flake8: noqa
        self.assertIn(result, [0, 2])
{% endfor %}  # flake8: noqa
    def tearDown(self):  # flake8: noqa
        self.env.revert_snapshot("before_test")

if __name__ == '__main__':
    unittest.main()

{# Enable this to get a debug list with all template values
{% include 'debug_template.txt' %}
#}
