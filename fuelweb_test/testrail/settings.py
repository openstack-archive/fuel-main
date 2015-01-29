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

import logging
import os

logger = logging.getLogger(__package__)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


JENKINS = {
    'url': os.environ.get('JENKINS_URL', 'http://localhost/'),
}


class TestRailSettings():
    url = os.environ.get('TESTRAIL_URL', 'https://mirantis.testrail.com')
    user = os.environ.get('TESTRAIL_USER', 'user@example.com')
    password = os.environ.get('TESTRAIL_PASSWORD', 'password')
    project = os.environ.get('TESTRAIL_PROJECT', 'Mirantis OpenStack')
    milestone = os.environ.get('TESTRAIL_MILESTONE', '6.1')
    test_suite = os.environ.get('TESTRAIL_TEST_SUITE', 'Swarm')
    test_section = os.environ.get('TESTRAIL_TEST_SECTION', 'all cases')
    test_include = os.environ.get('TESTRAIL_TEST_INCLUDE', None)
    test_exclude = os.environ.get('TESTRAIL_TEST_EXCLUDE', None)
