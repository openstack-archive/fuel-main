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
from devops.helpers.helpers import SSHClient, wait, _wait
from paramiko import RSAKey
import re
from fuelweb_test.helpers import Ebtables
from fuelweb_test.integration.base_test_case import BaseTestCase
from fuelweb_test.integration.decorators import debug
from fuelweb_test.nailgun_client import NailgunClient
from fuelweb_test.settings import CLEAN

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class BaseNodeTestCase(BaseTestCase):

    def setUp(self):
        if CLEAN:
            self.ci().get_empty_state()
        self.client = NailgunClient(self.get_admin_node_ip())

    @logwrap
    def get_interface_description(self, ctrl_ssh, interface_short_name):
        return ''.join(
            ctrl_ssh.execute(
                '/sbin/ip addr show dev %s' % interface_short_name
            )['stdout']
        )

    def assertNetworkConfiguration(self, node):
        remote = SSHClient(node['ip'], username='root', password='r00tme',
                           private_keys=self.get_private_keys())
        for interface in node['network_data']:
            if interface.get('vlan') is None:
                continue  # todo excess check fix interface json format
            interface_name = "%s.%s@%s" % (
                interface['dev'], interface['vlan'], interface['dev'])
            interface_short_name = "%s.%s" % (
                interface['dev'], interface['vlan'])
            interface_description = self.get_interface_description(
                remote, interface_short_name)
            self.assertIn(interface_name, interface_description)
            if interface.get('name') == 'floating':
                continue
            if interface.get('ip'):
                self.assertIn("inet %s" % interface.get('ip'),
                              interface_description)
            else:
                self.assertNotIn("inet ", interface_description)
            if interface.get('brd'):
                self.assertIn("brd %s" % interface['brd'],
                              interface_description)

    @logwrap
    def is_node_discovered(self, nailgun_node):
        return any(
            map(lambda node: node['mac'] == nailgun_node['mac']
                and node['status'] == 'discover', self.client.list_nodes()))

    @logwrap
    def delete_node(self, cluster_id, devops_node):
        nailgun_node = self.get_node_by_devops_node(devops_node)
        self.client.update_node(nailgun_node['id'], {'pending_deletion': True})
        task = self._launch_provisioning(cluster_id)
        self.assertTaskSuccess(task)
        return nailgun_node

    @logwrap
    def get_target_devs(self, devops_nodes):
        return [
            interface.target_dev for interface in [
                val for var in map(lambda node: node.interfaces, devops_nodes)
                for val in var]]

    @logwrap
    def get_ebtables(self, cluster_id, devops_nodes):
        return Ebtables(
            self.get_target_devs(devops_nodes),
            self.client._get_cluster_vlans(cluster_id))

    @logwrap
    def _get_common_vlan(self, cluster_id):
        """Find vlan that must be at all two nodes.
        """
        return self.client.get_networks(
            cluster_id)['networks'][0]['vlan_start']

    @logwrap
    def _run_network_verify(self, cluster_id):
        return self.client.verify_networks(
            cluster_id, self.client.get_networks(cluster_id)['networks'])

    @logwrap
    def check_role_file(self, nodes_dict):
        for node, role in self.get_nailgun_node_roles(nodes_dict):
            remote = SSHClient(
                node['ip'], username='root', password='r00tme',
                private_keys=self.get_private_keys())
            if role != "cinder":
                self.assertTrue(remote.isfile('/tmp/%s-file' % role))

    @logwrap
    def _basic_provisioning(self, cluster_name, nodes_dict, port=5514):
        self.client.clean_clusters()
        cluster_id = self.create_cluster(name=cluster_name)
        self.client.add_syslog_server(
            cluster_id, self.ci().get_host_node_ip(), port)
        node_names = []
        for role in nodes_dict:
            node_names += nodes_dict[role]
        if len(node_names) > 1:
            controller_amount = len(nodes_dict.get('controller', []))
            if controller_amount == 1:
                self.client.update_cluster(
                    cluster_id,
                    {"mode": "multinode"})
            if controller_amount > 1:
                self.client.update_cluster(cluster_id, {"mode": "ha"})

        nodes = self.bootstrap_nodes(self.devops_nodes_by_names(node_names))

        for node, role in self.get_nailgun_node_roles(nodes_dict):
            self.client.update_node(
                node['id'], {"role": role, "pending_addition": True})

        self.update_nodes_in_cluster(cluster_id, nodes)
        task = self._launch_provisioning(cluster_id)
        self.assertTaskSuccess(task)
        self.check_role_file(nodes_dict)
        return cluster_id

    @logwrap
    def get_nailgun_node_roles(self, nodes_dict):
        nailgun_node_roles = []
        for role in nodes_dict:
            for node_name in nodes_dict[role]:
                slave = self.ci().environment().node_by_name(node_name)
                node = self.get_node_by_devops_node(slave)
                nailgun_node_roles.append((node, role))
        return nailgun_node_roles

    @logwrap
    def _launch_provisioning(self, cluster_id):
        """Return hash with task description."""
        return self.client.update_cluster_changes(cluster_id)

    @logwrap
    def assertTaskSuccess(self, task, timeout=90 * 60):
        self.assertEquals('ready', self._task_wait(task, timeout)['status'])

    @logwrap
    def assertTaskFailed(self, task, timeout=70 * 60):
        self.assertEquals('error', self._task_wait(task, timeout)['status'])

    @logwrap
    def _task_wait(self, task, timeout):
        wait(
            lambda: self.client.get_task(
                task['id'])['status'] != 'running',
            timeout=timeout)
        return self.client.get_task(task['id'])

    @logwrap
    def _upload_sample_release(self):
        release_id = self.client.get_grizzly_release_id()
        if not release_id:
            raise Exception("Not implemented uploading of release")
        return release_id

    @logwrap
    def get_or_create_cluster(self, name, release_id):
        if not release_id:
            release_id = self._upload_sample_release()
        cluster_id = self.client.get_cluster_id(name)
        if not cluster_id:
            self.client.create_cluster(
                data={"name": name, "release": str(release_id)}
            )
            cluster_id = self.client.get_cluster_id(name)
        if not cluster_id:
            raise Exception("Could not get cluster '%s'" % name)
        return cluster_id

    @logwrap
    def create_cluster(self, name='default',
                       release_id=None, net_manager="FlatDHCPManager"):
        cluster_id = self.get_or_create_cluster(name, release_id)
        self.client.update_network(
            cluster_id,
            net_manager=net_manager)
        if net_manager == "VlanManager":
            flat_net = filter(
                lambda network: network['name'] == 'fixed',
                self.client.get_networks(cluster_id)['networks'])
            flat_net[0]['amount'] = 8
            flat_net[0]['network_size'] = 16
            self.client.update_network(cluster_id, flat_net=flat_net)
        return cluster_id

    @logwrap
    def update_nodes_in_cluster(self, cluster_id, nodes):
        node_ids = [str(node['id']) for node in nodes]
        self.client.update_cluster(cluster_id, {"nodes": node_ids})
        self.assertEquals(
            sorted(node_ids),
            sorted(map(
                lambda node: str(node['id']),
                self.client.list_cluster_nodes(cluster_id))))

    @logwrap
    def get_node_by_devops_node(self, devops_node):
        """Returns dict with nailgun slave node description if node is
        registered. Otherwise return None.
        """
        mac_addresses = map(
            lambda interface: interface.mac_address.capitalize(),
            devops_node.interfaces)
        for nailgun_node in self.client.list_nodes():
            if nailgun_node['mac'].capitalize() in mac_addresses:
                nailgun_node['devops_name'] = devops_node.name
                return nailgun_node
        return None

    def nailgun_nodes(self, devops_nodes):
        return map(lambda node: self.get_node_by_devops_node(node),
                   devops_nodes)

    def devops_nodes_by_names(self, devops_node_names):
        return map(lambda name: self.ci().environment().node_by_name(name),
                   devops_node_names)

    @logwrap
    def bootstrap_nodes(self, devops_nodes, timeout=600):
        """Start vms and wait they are registered on nailgun.
        :rtype : List of registred nailgun nodes
        """
        for node in devops_nodes:
            node.start()
        wait(lambda: all(self.nailgun_nodes(devops_nodes)), 15, timeout)
        return self.nailgun_nodes(devops_nodes)

    @logwrap
    def assert_service_list(self, remote, smiles_count):
        ret = remote.check_call('/usr/bin/nova-manage service list')
        self.assertEqual(
            smiles_count, ''.join(ret['stdout']).count(":-)"), "Smiles count")
        self.assertEqual(
            0, ''.join(ret['stdout']).count("XXX"), "Broken services count")

    @logwrap
    def assert_node_service_list(self, node_name, smiles_count):
        ip = self.get_node_by_devops_node(
            self.ci().environment().node_by_name(node_name))['ip']
        remote = SSHClient(ip, username='root', password='r00tme',
                           private_keys=self.get_private_keys())
        return self.assert_service_list(remote, smiles_count)

    @logwrap
    def assert_glance_index(self, ctrl_ssh):
        ret = ctrl_ssh.check_call('. /root/openrc; glance index')
        self.assertEqual(1, ''.join(ret['stdout']).count("TestVM"))

    @logwrap
    def assert_network_list(self, networks_count, remote):
        ret = remote.check_call('/usr/bin/nova-manage network list')
        self.assertEqual(networks_count + 1, len(ret['stdout']))

    @logwrap
    def assertClusterReady(self, node_name, smiles_count,
                           networks_count=1, timeout=300):
        _wait(
            lambda: self.get_cluster_status(
                self.get_node_by_devops_node(
                    self.ci().environment().node_by_name(node_name))['ip'],
                smiles_count=smiles_count,
                networks_count=networks_count),
            timeout=timeout)

    @logwrap
    def get_cluster_status(self, ip, smiles_count, networks_count=1):
        remote = SSHClient(ip, username='root', password='r00tme',
                           private_keys=self.get_private_keys())
        self.assert_service_list(remote, smiles_count)
        self.assert_glance_index(remote)
        self.assert_network_list(networks_count, remote)

    @logwrap
    def get_cluster_floating_list(self, ip):
        remote = SSHClient(ip, username='root', password='r00tme',
                           private_keys=self.get_private_keys())
        ret = remote.check_call('/usr/bin/nova-manage floating list')
        ret_str = ''.join(ret['stdout'])
        return re.findall('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ret_str)

    @logwrap
    def assert_cluster_floating_list(self, ip, expected_ips):
        current_ips = self.get_cluster_floating_list(ip)
        self.assertEqual(len(current_ips), len(expected_ips),
                         "Floating ips amount. Cluster ip: %s" % ip)

        absent_ips = []
        for ip in expected_ips:
            try:
                current_ips.index(ip)
                current_ips.remove(ip)
            except ValueError:
                absent_ips.append(ip)

        self.assertTrue(len(absent_ips) == 0 and len(current_ips) == 0,
                        'Floating ip list')

    @logwrap
    def get_private_keys(self):
        keys = []
        for key_string in ['/root/.ssh/id_rsa', '/root/.ssh/bootstrap.rsa']:
            with self.remote().open(key_string) as f:
                keys.append(RSAKey.from_private_key(f))
        return keys
