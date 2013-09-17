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


class TestNode(BaseNodeTestCase):
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_release_upload(self):
        self.prepare_environment()
        self._upload_sample_release()

    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_http_returns_no_error(self):
        self.prepare_environment()
        self.client.get_root()

    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_create_empty_cluster(self):
        self.prepare_environment()
        self.create_cluster(name='empty')

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_node_deploy(self):
        self.prepare_environment()
        self.bootstrap_nodes(self.nodes().slaves[:1])

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_updating_nodes_in_cluster(self):
        self.prepare_environment()
        cluster_id = self.create_cluster(name='empty')
        nodes = {'slave-01': ['controller']}
        self.bootstrap_nodes(self.nodes().slaves[:1])
        self.update_nodes(cluster_id, nodes)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_one_node_provisioning(self):
        self.prepare_environment()
        cluster_id = self.create_cluster(name="provision")
        self.basic_provisioning(
            cluster_id=cluster_id,
            nodes_dict={'slave-01': ['controller']}
        )
        self.run_OSTF(cluster_id=cluster_id, should_fail=12, should_pass=12)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_simple_cluster_flat(self):
        cluster_id = self.prepare_environment(settings={
            'nodes': {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        })
        self.assertClusterReady(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)
        self.get_ebtables(cluster_id, self.nodes().slaves[:2]).restore_vlans()
        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 2)
        self.run_OSTF(cluster_id=cluster_id, should_fail=6, should_pass=18)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_simple_cluster_vlan(self):
        self.prepare_environment()
        cluster_name = 'simple_vlan'
        nodes = {'slave-01': ['controller'], 'slave-02': ['compute']}
        cluster_id = self.create_cluster(name=cluster_name)
        self.update_vlan_network_fixed(cluster_id, amount=8, network_size=32)
        self.basic_provisioning(cluster_id, nodes)
        self.assertClusterReady(
            'slave-01', smiles_count=6, networks_count=8, timeout=300)
        self.get_ebtables(cluster_id, self.nodes().slaves[:2]).restore_vlans()
        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 2)
        self.run_OSTF(cluster_id=cluster_id, should_fail=6, should_pass=18)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_network_config(self):
        cluster_id = self.prepare_environment(settings={
            'nodes': {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        })
        slave = self.nodes().slaves[0]
        node = self.get_node_by_devops_node(slave)
        self.assertNetworkConfiguration(node)
        self.run_OSTF(cluster_id=cluster_id, should_fail=6, should_pass=18)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_node_deletion(self):
        cluster_id = self.prepare_environment(settings={
            'nodes': {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        })
        nailgun_nodes = self.update_nodes(
            cluster_id, {'slave-01': ['controller']}, False, True)
        task = self.deploy_cluster(cluster_id)
        self.assertTaskSuccess(task)
        nodes = filter(lambda x: x["pending_deletion"] is True, nailgun_nodes)
        self.assertTrue(
            len(nodes) == 1,
            "Verify 1 node has pending deletion status"
        )
        wait(lambda: self.is_node_discovered(
            nodes[0]),
            timeout=3 * 60
        )
        self.run_OSTF(cluster_id=cluster_id, should_fail=24, should_pass=0)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_network_verify_with_blocked_vlan(self):
        self.prepare_environment()
        cluster_name = 'net_verify'
        nodes_dict = {'slave-01': ['controller'], 'slave-02': ['compute']}

        cluster_id = self.create_cluster(name=cluster_name)
        devops_nodes = self.nodes().slaves[:2]
        self.bootstrap_nodes(devops_nodes)

        ebtables = self.get_ebtables(cluster_id, devops_nodes)
        ebtables.restore_vlans()
        self.update_nodes(cluster_id, nodes_dict)
        try:
            ebtables.block_first_vlan()
            task = self._run_network_verify(cluster_id)
            self.assertTaskFailed(task, 60 * 2)
        finally:
            ebtables.restore_first_vlan()

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_multinic_bootstrap_booting(self):
        self.prepare_environment()
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
    @attr(releases=['centos'], suite='simple')
    def test_simple_cluster_with_cinder(self):
        cluster_id = self.prepare_environment(settings={
            'nodes': {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['cinder']
            }
        })
        self.assertClusterReady(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)
        self.run_OSTF(cluster_id=cluster_id, should_fail=5, should_pass=19)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_add_compute_node(self):
        cluster_id = self.prepare_environment(settings={
            'nodes': {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        })

        self.bootstrap_nodes(self.nodes().slaves[2:3])
        self.update_nodes(cluster_id, {'slave-03': ['compute']}, True, False)

        task = self.client.deploy_cluster_changes(cluster_id)
        self.assertTaskSuccess(task)
        self.assertEqual(3, len(self.client.list_cluster_nodes(cluster_id)))

        self.assertClusterReady(
            self.nodes().slaves[0].name,
            smiles_count=8, networks_count=1, timeout=300)
        self.assert_node_service_list(self.nodes().slaves[1].name, 8)
        self.assert_node_service_list(self.nodes().slaves[2].name, 8)
        self.run_OSTF(cluster_id=cluster_id, should_fail=6, should_pass=18)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_floating_ips(self):
        self.prepare_environment()
        cluster_name = 'floating_ips'
        nodes_dict = {'slave-01': ['controller'], 'slave-02': ['compute']}
        self.bootstrap_nodes(self.nodes().slaves[:2])

        cluster_id = self.create_cluster(name=cluster_name)

        # set ip ranges for floating network
        networks = self.client.get_networks(cluster_id)
        for interface, network in enumerate(networks['networks']):
            if network['name'] == 'floating':
                networks['networks'][interface]['ip_ranges'] = [
                    ['240.0.0.2', '240.0.0.10'],
                    ['240.0.0.20', '240.0.0.25'],
                    ['240.0.0.30', '240.0.0.35']]
                break

        self.client.update_network(cluster_id,
                                   net_manager=networks['net_manager'],
                                   networks=networks['networks'])

        # adding nodes in cluster
        self.update_nodes(cluster_id, nodes_dict, True, False)
        task = self.deploy_cluster(cluster_id)
        self.assertTaskSuccess(task)

        # assert ips
        expected_ips = ['240.0.0.%s' % i for i in range(2, 11, 1)] + \
                       ['240.0.0.%s' % i for i in range(20, 26, 1)] + \
                       ['240.0.0.%s' % i for i in range(30, 36, 1)]
        self.assert_cluster_floating_list('slave-02', expected_ips)
        self.run_OSTF(cluster_id=cluster_id, should_fail=6, should_pass=18)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_node_disk_sizes(self):
        self.prepare_environment()
        # all nodes have 3 identical disks with same size
        nodes_dict = {
            'slave-01': ['controller'],
            'slave-02': ['compute'],
            'slave-03': ['cinder']
        }

        self.bootstrap_nodes(self.nodes().slaves[:3])

        # assert /api/nodes
        nailgun_nodes = self.client.list_nodes()
        for node in nailgun_nodes:
            for disk in node['meta']['disks']:
                self.assertEqual(disk['size'], 21474836480, 'Disk size')

        notifications = self.client.get_notifications()
        for node in nailgun_nodes:
            # assert /api/notifications
            for notification in notifications:
                if notification['node_id'] == node['id']:
                    self.assertIn('64.0 GB HDD', notification['message'])

            # assert disks
            disks = self.client.get_node_disks(node['id'])
            for disk in disks:
                self.assertEqual(disk['size'], 19980, 'Disk size')

        # deploy the cluster
        self.prepare_environment(settings={'nodes': nodes_dict})

        # assert node disks after deployment
        for node_name in nodes_dict:
            str_block_devices = self.get_cluster_block_devices(node_name)
            self.assertRegexpMatches(
                str_block_devices,
                'vda\s+252:0\s+0\s+20G\s+0\s+disk'
            )
            self.assertRegexpMatches(
                str_block_devices,
                'vdb\s+252:16\s+0\s+20G\s+0\s+disk'
            )
            self.assertRegexpMatches(
                str_block_devices,
                'vdc\s+252:32\s+0\s+20G\s+0\s+disk'
            )

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_node_multiple_interfaces(self):
        self.prepare_environment()
        cluster_name = 'node interfaces'
        interfaces_dict = {
            'eth0': ['management'],
            'eth1': ['floating', 'public'],
            'eth2': ['storage'],
            'eth3': ['fixed']
        }
        nodes_dict = {
            'slave-01': ['controller'],
            'slave-02': ['compute']
        }
        self.bootstrap_nodes(self.nodes().slaves[:2])

        cluster_id = self.create_cluster(name=cluster_name)
        self.update_nodes(cluster_id, nodes_dict, True, False)

        nailgun_nodes = self.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.update_node_networks(node['id'], interfaces_dict)

        task = self.deploy_cluster(cluster_id)
        self.assertTaskSuccess(task)

        nailgun_nodes = self.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.assertNetworkConfiguration(node)

        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 2)

    @snapshot_errors
    @logwrap
    @fetch_logs
    @attr(releases=['centos'], suite='simple')
    def test_untagged_network(self):
        cluster_name = 'simple_untagged'

        vlan_turn_off = {'vlan_start': None}
        nodes = {
            'slave-01': ['controller'],
            'slave-02': ['compute']
        }
        interfaces = {
            'eth0': [],
            'eth1': ["public", "floating",
                     "management", "storage",
                     "fixed"],
            'eth2': [],
            'eth3': []
        }

        self.prepare_environment()

        # create a new empty cluster and add nodes to it:
        cluster_id = self.create_cluster(name=cluster_name)
        self.bootstrap_nodes(self.nodes().slaves[:2])
        self.update_nodes(cluster_id, nodes)

        # assign all networks to second network interface:
        nets = self.client.get_networks(cluster_id)['networks']
        nailgun_nodes = self.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.update_node_networks(node['id'], interfaces)

        # select networks that will be untagged:
        [net.update(vlan_turn_off) for net in nets]

        # stop using VLANs:
        self.client.update_network(cluster_id,
                                   networks=nets)

        # run network check:
        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 5)

        # deploy cluster:
        task = self.deploy_cluster(cluster_id)
        self.assertTaskSuccess(task)

        #run network check again:
        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 5)

    @logwrap
    @fetch_logs
    @attr(releases=['redhat'], suite='simple')
    def test_download_redhat(self):
        self.prepare_environment()

        # download redhat repo from local place to boost the test
        # remote = self.nodes().admin.remote('internal', 'root', 'r00tme')
        # remote.execute('wget -q http://172.18.67.168/rhel6/rhel-rpms.tar.gz')
        # remote.execute('tar xzf rhel-rpms.tar.gz -C /')

        self.update_redhat_credentials('rhn')
        self.assert_release_state('RHOS', state='available')
        # self.ci().environment().snapshot(
        #     name=EMPTY_SNAPSHOT, description=EMPTY_SNAPSHOT, force=True)

if __name__ == '__main__':
    unittest.main()
