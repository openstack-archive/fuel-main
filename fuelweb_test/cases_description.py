#    Copyright 2015 Mirantis, Inc.
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

import os
import re

from testrail import APIClient


def get_tests_descriptions():
    # List of modules for import should be copied from run_tests.py
    from proboscis import TestProgram  # noqa
    from tests import test_admin_node  # noqa
    from tests import test_ceph  # noqa
    from tests import test_environment_action  # noqa
    from tests import test_ha  # noqa
    from tests import test_neutron  # noqa
    from tests import test_pullrequest  # noqa
    from tests import test_services  # noqa
    from tests import test_simple  # noqa
    from tests import test_vcenter  # noqa
    from tests.tests_strength import test_failover  # noqa
    from tests.tests_strength import test_master_node_failover  # noqa
    from tests.tests_strength import test_ostf_repeatable_tests  # noqa
    from tests.tests_strength import test_restart  # noqa
    from tests.tests_strength import test_huge_environments  # noqa
    from tests.tests_strength import test_image_based  # noqa
    from tests import test_bonding  # noqa
    from tests.tests_strength import test_neutron  # noqa
    from tests import test_zabbix  # noqa
    from tests import test_upgrade  # noqa
    from tests.plugins.plugin_example import test_fuel_plugin_example  # noqa
    from tests.plugins.plugin_glusterfs import test_plugin_glusterfs  # noqa
    from tests.plugins.plugin_lbaas import test_plugin_lbaas  # noqa
    from tests import test_multiple_networks  # noqa

    tests = []

    for case in TestProgram().cases:
            docstring = case.entry.home.func_doc or ''
            docstring = '\n'.join([s.strip() for s in docstring.split('\n')])

            steps = [{"content": s, "expected": "pass"} for s in
                     docstring.split('\n') if s and s[0].isdigit()]

            test_duration = re.search(r'Duration\s+(\d+[s,m])\b', docstring)
            test_case = {
                "title": docstring.split('\n')[0] or case.entry.home.func_name,
                "type_id": 1,
                "priority_id": 5,
                "estimate": test_duration.group(1) if test_duration else "3m",
                "refs": "",
                "custom_test_group": case.entry.home.func_name,
                "custom_test_case_description": docstring or " ",
                "custom_test_case_steps": steps
            }
            tests.append(test_case)
    return tests


def upload_tests_descriptions(client, tests, section_id):
    for test in tests:
        client.send_post('add_case/{0}'.format(section_id), test)


if __name__ == '__main__':
    testrail_client = APIClient("https://mirantis.testrail.com/")
    testrail_client.user = os.environ.get('TESTRAIL_USER', 'user@example.com')
    testrail_client.password = os.environ.get('TESTRAIL_PASSWORD', 'password')
    testrail_section_id = os.environ.get('TESTRAIL_SECTION_ID', '1')
    upload_tests_descriptions(client=testrail_client,
                              tests=get_tests_descriptions(),
                              section_id=testrail_section_id)
