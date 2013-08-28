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
from fuelweb_test.integration.base_node_test_case import BaseNodeTestCase
from fuelweb_test.integration.decorators import snapshot_errors, \
    debug, fetch_logs

logging.basicConfig(
    format=':%(lineno)d: %(asctime)s %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class TestNode(BaseNodeTestCase):
    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_ha_cluster_vlan(self):
        self.prepare_environment()
        cluster_name = 'ha_vlan'
        nodes = {
            'controller': ['slave-01', 'slave-02', 'slave-03'],
            'compute': ['slave-04', 'slave-05']
        }
        cluster_id = self.create_cluster(name=cluster_name)
        self.update_vlan_network_fixed(cluster_id, amount=8, network_size=32)
        self._basic_provisioning(cluster_id, nodes)
        self.assertClusterReady(
            'slave-01', smiles_count=16, networks_count=8, timeout=300)
        self.get_ebtables(cluster_id, self.nodes().slaves[:5]).restore_vlans()
        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 2)
        self.assertOSTFRunSuccess(cluster_id, 6, 18)

if __name__ == '__main__':
    unittest.main()
