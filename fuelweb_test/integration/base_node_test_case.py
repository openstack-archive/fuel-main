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
import hashlib
from fuelweb_test.helpers import Ebtables
from fuelweb_test.integration.base_test_case import BaseTestCase
from fuelweb_test.integration.decorators import debug
from fuelweb_test.nailgun_client import NailgunClient
from fuelweb_test.settings import CLEAN, NETWORK_MANAGERS, EMPTY_SNAPSHOT, \
    REDHAT_USERNAME, REDHAT_PASSWORD, REDHAT_SATELLITE_HOST, \
    REDHAT_ACTIVATION_KEY

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class BaseNodeTestCase(BaseTestCase):

    environment_states = {}

    def setUp(self):
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
        for node, roles in self.get_nailgun_node_roles(nodes_dict):
            remote = SSHClient(
                node['ip'], username='root', password='r00tme',
                private_keys=self.get_private_keys())
            for role in roles:
                if role != "cinder":
                    self.assertTrue(remote.isfile('/tmp/%s-file' % role))

    @logwrap
    def clean_clusters(self):
        self.client.clean_clusters()

    @logwrap
    def update_deployment_mode(self, cluster_id, nodes_dict):
        controller_names = filter(
            lambda x: 'controller' in nodes_dict[x], nodes_dict)
        if len(nodes_dict) > 1:
            controller_amount = len(controller_names)
            if controller_amount == 1:
                self.client.update_cluster(
                    cluster_id,
                    {"mode": "multinode"})
            if controller_amount > 1:
                self.client.update_cluster(cluster_id, {"mode": "ha"})

    @logwrap
    def configure_cluster(self, cluster_id, nodes_dict):
        self.update_deployment_mode(cluster_id, nodes_dict)
        self.update_nodes(cluster_id, nodes_dict, True, False)
        # TODO: update network configuration

    @logwrap
    def basic_provisioning(self, cluster_id, nodes_dict, port=5514):
        self.client.add_syslog_server(
            cluster_id, self.ci().get_host_node_ip(), port)

        self.bootstrap_nodes(self.devops_nodes_by_names(nodes_dict.keys()))
        self.configure_cluster(cluster_id, nodes_dict)

        task = self.deploy_cluster(cluster_id)
        self.assertTaskSuccess(task)
        self.check_role_file(nodes_dict)
        return cluster_id

    @logwrap
    def prepare_environment(self, name='cluster_name', settings={}):
        state_hash = hashlib.md5(str(settings)).hexdigest()
        empty_state_hash = hashlib.md5(str({})).hexdigest()
        if state_hash == empty_state_hash:
            # revert to empty state
            self.ci().get_empty_environment()
        elif state_hash in self.environment_states:
            # revert virtual machines
            state = self.environment_states[state_hash]
            self.ci().get_state(state['snapshot_name'])
            self.ci().environment().resume()
        else:
            # create cluster
            self.ci().get_empty_environment()
            cluster_id = self.create_cluster(name=name)
            self.basic_provisioning(cluster_id, settings['nodes'])

            # make a snapshot
            snapshot_name = '%s_%s' % \
                            (name.replace(' ', '_')[:17], state_hash)
            self.ci().environment().suspend(verbose=False)
            self.ci().environment().snapshot(
                name=snapshot_name,
                description=name,
                force=True,
            )
            self.ci().environment().resume(verbose=False)
            self.environment_states[state_hash] = {
                'snapshot_name': snapshot_name,
                'cluster_name': name,
                'settings': settings
            }

        # return id of last created cluster
        clusters = self.client.list_clusters()
        if len(clusters) > 0:
            return clusters.pop()['id']
        return None

    @logwrap
    def get_nailgun_node_roles(self, nodes_dict):
        nailgun_node_roles = []
        for node_name in nodes_dict:
            slave = self.ci().environment().node_by_name(node_name)
            node = self.get_node_by_devops_node(slave)
            nailgun_node_roles.append((node, nodes_dict[node_name]))
        return nailgun_node_roles

    @logwrap
    def deploy_cluster(self, cluster_id):
        """Return hash with task description."""
        return self.client.deploy_cluster_changes(cluster_id)

    @logwrap
    def assertTaskSuccess(self, task, timeout=90 * 60):
        self.assertEquals('ready', self._task_wait(task, timeout)['status'])

    @logwrap
    def assertTaskFailed(self, task, timeout=70 * 60):
        self.assertEquals('error', self._task_wait(task, timeout)['status'])

    @logwrap
    def assertOSTFRunSuccess(self, cluster_id, should_fail=0, should_pass=0,
                             timeout=10 * 60):
        set_result_list = self._ostf_test_wait(cluster_id, timeout)

        passed = 0
        failed = 0
        for set_result in set_result_list:
            passed += len(filter(lambda test: test['status'] == 'success',
                                 set_result['tests']))
            failed += len(
                filter(
                    lambda test: test['status'] == 'failure' or
                    test['status'] == 'error',
                    set_result['tests']
                )
            )
        self.assertEqual(passed, should_pass, 'Passed tests')
        self.assertEqual(failed, should_fail, 'Failed tests')

    @logwrap
    def run_OSTF(self, cluster_id, test_sets=None,
                 should_fail=0, should_pass=0):
        test_sets = test_sets \
            if test_sets is not None \
            else ['fuel_smoke', 'fuel_sanity']

        self.client.ostf_run_tests(cluster_id, test_sets)
        self.assertOSTFRunSuccess(cluster_id, should_fail=should_fail,
                                  should_pass=should_pass)

    @logwrap
    def _task_wait(self, task, timeout):
        wait(
            lambda: self.client.get_task(
                task['id'])['status'] != 'running',
            timeout=timeout)
        return self.client.get_task(task['id'])

    @logwrap
    def _ostf_test_wait(self, cluster_id, timeout):
        wait(
            lambda: all([run['status'] == 'finished'
                         for run in
                         self.client.get_ostf_test_run(cluster_id)]),
            timeout=timeout)
        return self.client.get_ostf_test_run(cluster_id)

    @logwrap
    def _tasks_wait(self, tasks, timeout):
        return [self._task_wait(task, timeout) for task in tasks]

    @logwrap
    def _upload_sample_release(self):
        release_id = self.client.get_release_id()
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
    def create_cluster(self, name='default', release_id=None):
        """
        :param name:
        :param release_id:
        :return: cluster_id
        """
        return self.get_or_create_cluster(name, release_id)

    @logwrap
    def update_nodes(self, cluster_id, nodes_dict,
                     pending_addition=True, pending_deletion=False):
        # update nodes in cluster
        nodes_data = []
        for node_name in nodes_dict:
            devops_node = self.ci().environment().node_by_name(node_name)
            node = self.get_node_by_devops_node(devops_node)
            node_data = {'cluster_id': cluster_id, 'id': node['id'],
                         'pending_addition': pending_addition,
                         'pending_deletion': pending_deletion,
                         'pending_roles': nodes_dict[node_name]}
            nodes_data.append(node_data)

        # assume nodes are going to be updated for one cluster only
        cluster_id = nodes_data[-1]['cluster_id']
        node_ids = [str(node_info['id']) for node_info in nodes_data]
        self.client.update_nodes(nodes_data)

        nailgun_nodes = self.client.list_cluster_nodes(cluster_id)
        cluster_node_ids = map(lambda node: str(node['id']), nailgun_nodes)
        self.assertTrue(
            all([node_id in cluster_node_ids for node_id in node_ids]))
        return nailgun_nodes

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
    def _get_remote(self, ip):
        return SSHClient(ip, username='root', password='r00tme',
                         private_keys=self.get_private_keys())

    @logwrap
    def _get_remote_for_node(self, node_name):
        ip = self.get_node_by_devops_node(
            self.ci().environment().node_by_name(node_name))['ip']
        return self._get_remote(ip)

    @logwrap
    def get_cluster_status(self, ip, smiles_count, networks_count=1):
        remote = self._get_remote(ip)
        self.assert_service_list(remote, smiles_count)
        self.assert_glance_index(remote)
        self.assert_network_list(networks_count, remote)

    @logwrap
    def get_cluster_floating_list(self, node_name):
        remote = self._get_remote_for_node(node_name)
        ret = remote.check_call('/usr/bin/nova-manage floating list')
        ret_str = ''.join(ret['stdout'])
        return re.findall('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ret_str)

    @logwrap
    def get_cluster_block_devices(self, node_name):
        remote = self._get_remote_for_node(node_name)
        ret = remote.check_call('/bin/lsblk')
        return ''.join(ret['stdout'])

    @logwrap
    def assert_cluster_floating_list(self, node_name, expected_ips):
        current_ips = self.get_cluster_floating_list(node_name)
        self.assertEqual(set(expected_ips), set(current_ips))

    @logwrap
    def get_private_keys(self):
        keys = []
        for key_string in ['/root/.ssh/id_rsa', '/root/.ssh/bootstrap.rsa']:
            with self.remote().open(key_string) as f:
                keys.append(RSAKey.from_private_key(f))
        return keys

    @logwrap
    def update_node_networks(self, node_id, interfaces_dict):
        interfaces = self.client.get_node_interfaces(node_id)
        for interface in interfaces:
            interface_name = interface['name']
            interface['assigned_networks'] = []
            for allowed_network in interface['allowed_networks']:
                key_exists = interface_name in interfaces_dict
                if key_exists and \
                        allowed_network['name'] \
                        in interfaces_dict[interface_name]:
                    interface['assigned_networks'].append(allowed_network)

        self.client.put_node_interfaces(
            [{'id': node_id, 'interfaces': interfaces}])

    @logwrap
    def update_vlan_network_fixed(
            self, cluster_id, amount=1, network_size=256):
        network_list = self.client.get_networks(cluster_id)['networks']
        for network in network_list:
            if network["name"] == 'fixed':
                network['amount'] = amount
                network['network_size'] = network_size

        self.client.update_network(
            cluster_id,
            networks=network_list,
            net_manager=NETWORK_MANAGERS['vlan'])

    @logwrap
    def update_redhat_credentials(
            self, license_type,
            username=REDHAT_USERNAME, password=REDHAT_PASSWORD,
            satellite_host=REDHAT_SATELLITE_HOST,
            activation_key=REDHAT_ACTIVATION_KEY):

        # release name is in environment variable OPENSTACK_RELEASE
        release_id = self.client.get_release_id('RHOS')
        self.client.update_redhat_setup({
            "release_id": release_id,
            "username": username,
            "license_type": license_type,
            "satellite": satellite_host,
            "password": password,
            "activation_key": activation_key})
        tasks = self.client.get_tasks()
        # wait for 'redhat_setup' task only. Front-end works same way
        for task in tasks:
            if task['name'] == 'redhat_setup' \
                    and task['result']['release_info']['release_id'] \
                            == release_id:
                return self._task_wait(task, 60 * 120)

    def assert_release_state(self, release_name, state='available'):
        for release in self.client.get_releases():
            if release["name"].find(release_name) != -1:
                self.assertEqual(release['state'], state)
                return release["id"]
