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
import re

from devops.helpers.helpers import SSHClient, wait, _wait
from proboscis.asserts import assert_true, assert_false, assert_equal
from fuelweb_test.helpers.ci import *

from fuelweb_test.helpers.decorators import debug
from fuelweb_test.models.nailgun_client import NailgunClient
from fuelweb_test.settings import *


logger = logging.getLogger(__name__)
logwrap = debug(logger)

DEPLOYMENT_MODE_SIMPLE = "multinode"
DEPLOYMENT_MODE_HA = "ha_compact"


class FuelWebClient(object):

    def __init__(self, admin_node_ip, environment):
        self.admin_node_ip = admin_node_ip
        self.client = NailgunClient(admin_node_ip)
        self._environment = environment
        super(FuelWebClient, self).__init__()

    @property
    def environment(self):
        """
        :rtype: EnvironmentModel
        """
        return self._environment

    @staticmethod
    @logwrap
    def get_cluster_status(ssh_remote, smiles_count, networks_count=1):
        verify_service_list(ssh_remote, smiles_count)
        verify_glance_index(ssh_remote)
        verify_network_list(networks_count, ssh_remote)

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
        return [self.task_wait(task, timeout) for task in tasks]

    @logwrap
    def add_syslog_server(self, cluster_id, host, port):
        self.client.add_syslog_server(cluster_id, host, port)

    @logwrap
    def assert_cluster_floating_list(self, node_name, expected_ips):
        current_ips = self.get_cluster_floating_list(node_name)
        assert_equal(set(expected_ips), set(current_ips))

    @logwrap
    def assert_cluster_ready(self, node_name, smiles_count,
                             networks_count=1, timeout=300):
        remote = self.environment.get_ssh_to_remote(
            self.get_nailgun_node_by_devops_node(
                self.environment.get_virtual_environment().
                node_by_name(node_name))['ip']
        )
        _wait(
            lambda: self.get_cluster_status(
                remote,
                smiles_count=smiles_count,
                networks_count=networks_count),
            timeout=timeout)

    @logwrap
    def assert_ostf_run(self, cluster_id, should_fail=0, should_pass=0,
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
        assert_true(
            passed >= should_pass, 'Passed tests, pass: {}'.format(passed)
        )
        assert_true(
            failed <= should_fail, 'Failed tests,  fails: {}'.format(failed)
        )

    def assert_release_state(self, release_name, state='available'):
        for release in self.client.get_releases():
            if release["name"].find(release_name) != -1:
                assert_equal(release['state'], state)
                return release["id"]

    @logwrap
    def assert_task_success(self, task, timeout=90 * 60, interval=5):
        assert_equal(
            'ready',
            self.task_wait(task, timeout, interval)['status']
        )

    @logwrap
    def assert_task_failed(self, task, timeout=70 * 60, interval=5):
        assert_equal(
            'error',
            self.task_wait(task, timeout, interval)['status']
        )

    @logwrap
    def create_cluster(self,
                       name,
                       settings=None,
                       release_name=OPENSTACK_RELEASE,
                       mode=DEPLOYMENT_MODE_SIMPLE,
                       port=5514):
        """
        :param name:
        :param release_name:
        :param mode:
        :param settings:
        :param port:
        :return: cluster_id
        """
        release_id = self.client.get_release_id(release_name=release_name)

        if settings is None:
            settings = {}

        cluster_id = self.client.get_cluster_id(name)
        if not cluster_id:
            data = {
                "name": name,
                "release": str(release_id),
                "mode": mode
            }

            if "net_provider" in settings:
                data.update(
                    {
                        'net_provider': settings["net_provider"],
                        'net_segment_type': settings["net_segment_type"]
                    }
                )

            self.client.create_cluster(data=data)
            cluster_id = self.client.get_cluster_id(name)

            attributes = self.client.get_cluster_attributes(cluster_id)

            for option in settings:
                section = False
                if option in ('savanna', 'murano'):
                    section = 'additional_components'
                if option in ('volumes_ceph', 'images_ceph'):
                    section = 'storage'
                if section:
                    attributes['editable'][section][option]['value'] =\
                        settings[option]

            self.client.update_cluster_attributes(cluster_id, attributes)

        if not cluster_id:
            raise Exception("Could not get cluster '%s'" % name)

        self.client.add_syslog_server(
            cluster_id, self.environment.get_host_node_ip(), port)

        return cluster_id

    def deploy_cluster_wait(self, cluster_id):
        task = self.deploy_cluster(cluster_id)
        self.assert_task_success(task, interval=30)

    @logwrap
    def deploy_cluster(self, cluster_id):
        """Return hash with task description."""
        return self.client.deploy_cluster_changes(cluster_id)

    @logwrap
    def get_cluster_floating_list(self, node_name):
        remote = self.get_ssh_for_node(node_name)
        ret = remote.check_call('/usr/bin/nova-manage floating list')
        ret_str = ''.join(ret['stdout'])
        return re.findall('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ret_str)

    @logwrap
    def get_cluster_block_devices(self, node_name):
        remote = self.get_ssh_for_node(node_name)
        ret = remote.check_call('/bin/lsblk')
        return ''.join(ret['stdout'])

    @logwrap
    def get_last_created_cluster(self):
        # return id of last created cluster
        clusters = self.client.list_clusters()
        if len(clusters) > 0:
            return clusters.pop()['id']
        return None

    @logwrap
    def get_nailgun_node_roles(self, nodes_dict):
        nailgun_node_roles = []
        for node_name in nodes_dict:
            slave = self.environment.get_virtual_environment().\
                node_by_name(node_name)
            node = self.get_nailgun_node_by_devops_node(slave)
            nailgun_node_roles.append((node, nodes_dict[node_name]))
        return nailgun_node_roles

    @logwrap
    def get_nailgun_node_by_name(self, node_name):
        return self.get_nailgun_node_by_devops_node(
            self.environment.get_virtual_environment().node_by_name(node_name))

    @logwrap
    def get_nailgun_node_by_devops_node(self, devops_node):
        """
        Returns dict with nailgun slave node description if node is
        registered. Otherwise return None.
        """
        mac_addresses = map(
            lambda interface: interface.mac_address.capitalize(),
            devops_node.interfaces
        )
        for nailgun_node in self.client.list_nodes():
            if nailgun_node['mac'].capitalize() in mac_addresses:
                nailgun_node['devops_name'] = devops_node.name
                return nailgun_node

        return None

    @logwrap
    def get_ssh_for_node(self, node_name):
        ip = self.get_nailgun_node_by_devops_node(
            self.environment.get_virtual_environment().
            node_by_name(node_name))['ip']
        return self.environment.get_ssh_to_remote(ip)

    @logwrap
    def get_ssh_for_role(self, nodes_dict, role):
        node_name = sorted(filter(lambda name: role in nodes_dict[name],
                           nodes_dict.keys()))[0]
        return self.get_ssh_for_node(node_name)

    @logwrap
    def is_node_discovered(self, nailgun_node):
        return any(
            map(lambda node: node['mac'] == nailgun_node['mac']
                and node['status'] == 'discover', self.client.list_nodes()))

    @logwrap
    def run_network_verify(self, cluster_id):
        return self.client.verify_networks(
            cluster_id, self.client.get_networks(cluster_id)['networks'])

    @logwrap
    def run_ostf(self, cluster_id, test_sets=None,
                 should_fail=0, should_pass=0):
        test_sets = test_sets \
            if test_sets is not None \
            else ['smoke', 'sanity']

        self.client.ostf_run_tests(cluster_id, test_sets)
        self.assert_ostf_run(
            cluster_id,
            should_fail=should_fail,
            should_pass=should_pass
        )

    @logwrap
    def task_wait(self, task, timeout, interval=5):
        wait(
            lambda: self.client.get_task(
                task['id'])['status'] != 'running',
            interval=interval,
            timeout=timeout
        )
        return self.client.get_task(task['id'])

    @logwrap
    def update_nodes(self, cluster_id, nodes_dict,
                     pending_addition=True, pending_deletion=False):
        # update nodes in cluster
        nodes_data = []
        for node_name in nodes_dict:
            devops_node = self.environment.get_virtual_environment().\
                node_by_name(node_name)
            node = self.get_nailgun_node_by_devops_node(devops_node)
            node_data = {
                'cluster_id': cluster_id,
                'id': node['id'],
                'pending_addition': pending_addition,
                'pending_deletion': pending_deletion,
                'pending_roles': nodes_dict[node_name],
                'name': '{}_{}'.format(
                    node_name,
                    "_".join(nodes_dict[node_name])
                )
            }
            nodes_data.append(node_data)

        # assume nodes are going to be updated for one cluster only
        cluster_id = nodes_data[-1]['cluster_id']
        node_ids = [str(node_info['id']) for node_info in nodes_data]
        self.client.update_nodes(nodes_data)

        nailgun_nodes = self.client.list_cluster_nodes(cluster_id)
        cluster_node_ids = map(lambda _node: str(_node['id']), nailgun_nodes)
        assert_true(
            all([node_id in cluster_node_ids for node_id in node_ids]))
        return nailgun_nodes

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
    def update_redhat_credentials(
            self, license_type=REDHAT_LICENSE_TYPE,
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
                return self.task_wait(task, 60 * 120)

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
    def verify_murano_service(self, node_name):
        ip = self.get_nailgun_node_by_devops_node(
            self.environment.get_virtual_environment().
            node_by_name(node_name))['ip']
        verify_murano_service(self.environment.get_ssh_to_remote(ip))

    @logwrap
    def verify_network(self, cluster_id):
        task = self.run_network_verify(cluster_id)
        self.assert_task_success(task, 60 * 2, interval=10)

    @logwrap
    def verify_savanna_service(self, node_name):
        ip = self.get_nailgun_node_by_devops_node(
            self.environment.get_virtual_environment().
            node_by_name(node_name))['ip']
        verify_savanna_service(self.environment.get_ssh_to_remote(ip))
