#    Copyright 2013 Mirantis, Inc.
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
import unittest
from devops.helpers.helpers import wait
from nose.plugins.attrib import attr
from fuelweb_test.helpers import Ebtables
from fuelweb_test.integration.base_node_test_case import BaseNodeTestCase
from fuelweb_test.integration.decorators import snapshot_errors, \
    debug, fetch_logs
from fuelweb_test.settings import EMPTY_SNAPSHOT

logging.basicConfig(
    format=':%(lineno)d: %(asctime)s %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class TestPlatformSavanna(BaseNodeTestCase):

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos', "ubuntu"], test_thread='thread_1')
    def test_savanna(self):
        cluster_id = self.prepare_environment(settings={
            'nodes': {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
            },
            'savanna': True

        })

        self.assertClusterReady(
            'slave-01', smiles_count=6, networks_count=1, timeout=500)
        self.assert_savanna_service(self.nodes().slaves[0].name)
        self.assert_savanna_image_import(self.nodes().slaves[0].name)
        self.run_OSTF(cluster_id=cluster_id, test_sets='platform_tests', should_fail=0, should_pass=1)


if __name__ == '__main__':
    unittest.main()
