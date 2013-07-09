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


class TestNode(BaseNodeTestCase):
    @logwrap
    @fetch_logs
    def test_release_upload(self):
        self._upload_sample_release()

    @logwrap
    @fetch_logs
    def test_http_returns_no_error(self):
        self.client.get_root()

    @logwrap
    @fetch_logs
    def test_create_empty_cluster(self):
        self.create_cluster(name='empty')

    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_node_deploy(self):
        self.bootstrap_nodes(self.devops_nodes_by_names(['slave-01']))

    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_updating_nodes_in_cluster(self):
        cluster_id = self.create_cluster(name='empty')
        nodes = self.bootstrap_nodes(self.devops_nodes_by_names(['slave-01']))
        self.update_nodes_in_cluster(cluster_id, nodes)

    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_one_node_provisioning(self):
        self.client.clean_clusters()
        self._basic_provisioning('provision', {'controller': ['slave-01']})

    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_simple_cluster_flat(self):
        cluster_name = 'simple_flat'
        nodes = {'controller': ['slave-01'], 'compute': ['slave-02']}
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        self.assertClusterReady(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)
        self.get_ebtables(cluster_id, self.nodes().slaves[:2]).restore_vlans()
        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 2)

    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_simple_cluster_vlan(self):
        cluster_name = 'simple_vlan'
        nodes = {'controller': ['slave-01'], 'compute': ['slave-02']}
        self.create_cluster(name=cluster_name, net_manager="VlanManager")
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        self.assertClusterReady(
            'slave-01', smiles_count=6, networks_count=8, timeout=300)
        self.get_ebtables(cluster_id, self.nodes().slaves[:2]).restore_vlans()
        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 2)

    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_network_config(self):
        self.client.clean_clusters()
        self._basic_provisioning(
            'network_config', {'controller': ['slave-01']})
        slave = self.nodes().slaves[0]
        node = self.get_node_by_devops_node(slave)
        self.assertNetworkConfiguration(node)

    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_node_deletion(self):
        cluster_name = 'node_deletion'
        slave = self.nodes().slaves[0]
        nodes_dict = {'controller': [slave.name]}
        cluster_id = self._basic_provisioning(
            cluster_name=cluster_name, nodes_dict=nodes_dict)
        nailgun_node = self.delete_node(cluster_id, slave)
        wait(lambda: self.is_node_discovered(nailgun_node), timeout=3 * 60)

    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_network_verify_with_blocked_vlan(self):
        cluster_name = 'net_verify'
        cluster_id = self.create_cluster(name=cluster_name)
        devops_nodes = self.devops_nodes_by_names(['slave-01', 'slave-02'])
        nailgun_slave_nodes = self.bootstrap_nodes(devops_nodes)
        ebtables = self.get_ebtables(cluster_id, devops_nodes)
        ebtables.restore_vlans()
        self.update_nodes_in_cluster(cluster_id, nailgun_slave_nodes)
        try:
            ebtables.block_first_vlan()
            task = self._run_network_verify(cluster_id)
            self.assertTaskFailed(task, 60 * 2)
        finally:
            ebtables.restore_first_vlan()

    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_multinic_bootstrap_booting(self):
        slave = self.nodes().slaves[0]
        mac_addresses = [interface.mac_address for interface in
                         slave.interfaces.filter(network__name='internal')]
        try:
            for mac in mac_addresses:
                Ebtables.block_mac(mac)
            for mac in mac_addresses:
                Ebtables.restore_mac(mac)
                slave.destroy(verbose=False)
                self.nodes().admins[0].revert(EMPTY_SNAPSHOT)
                nailgun_slave = self.bootstrap_nodes([slave])[0]
                self.assertEqual(mac.upper(), nailgun_slave['mac'].upper())
                Ebtables.block_mac(mac)
        finally:
            for mac in mac_addresses:
                Ebtables.restore_mac(mac)

    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_simple_cluster_with_cinder(self):
        cluster_name = 'simple_with_cinder'
        nodes = {
            'controller': ['slave-01'],
            'compute': ['slave-02'],
            'cinder': ['slave-03']
        }
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        self.assertClusterReady(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)


    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_add_compute_node(self):
        cluster_name = 'node_addition'
        nodes_dict = {'controller': [n.name
                                     for n in self.nodes().slaves[:1]],
                      'compute': [n.name
                                  for n in self.nodes().slaves[1:2]]}
        additional_nodes_dict = \
            {'compute': [n.name for n in self.nodes().slaves[2:3]]}

        cluster_id = self._basic_provisioning(
            cluster_name=cluster_name, nodes_dict=nodes_dict)

        nodes = self.bootstrap_nodes(self.nodes().slaves[2:3])
        self.add_node(additional_nodes_dict)
        self.update_nodes_in_cluster(cluster_id, nodes)

        self.assertEqual(3, len(self.client.list_cluster_nodes(cluster_id)))
        task = self.client.update_cluster_changes(cluster_id)
        self.assertTaskSuccess(task)

        self.assertClusterReady(
            self.nodes().slaves[1:2],
            smiles_count=6, networks_count=1, timeout=300)
        self.assertClusterReady(
            self.nodes().slaves[1:2],
            smiles_count=6, networks_count=1, timeout=300)
        self.assertClusterReady(
            self.nodes().slaves[2:3],
            smiles_count=6, networks_count=1, timeout=300)

if __name__ == '__main__':
    unittest.main()
