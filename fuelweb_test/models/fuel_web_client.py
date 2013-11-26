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
from devops.error import TimeoutError

from devops.helpers.helpers import wait, _wait
from ipaddr import IPNetwork
from proboscis.asserts import assert_true, assert_equal
from fuelweb_test.helpers.checkers import *

from fuelweb_test.helpers.decorators import debug
from fuelweb_test.models.nailgun_client import NailgunClient
from fuelweb_test.settings import DEPLOYMENT_MODE_SIMPLE, NEUTRON, NEUTRON_SEGMENT
import fuelweb_test.settings as help_data


logger = logging.getLogger(__name__)
logwrap = debug(logger)


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
            passed >= should_pass, 'Passed tests, pass: {} should pass: {}'
                                   ''.format(passed, should_pass))
        assert_true(
            failed <= should_fail, 'Failed tests,  fails: {} should fail: {}'
                                   ''.format(failed, should_fail))

    def assert_release_state(self, release_name, state='available'):
        for release in self.client.get_releases():
            if release["name"].find(release_name) != -1:
                assert_equal(release['state'], state)
                return release["id"]

    @logwrap
    def assert_task_success(self, task, timeout=90 * 60, interval=5):
        task = self.task_wait(task, timeout, interval)
        assert_equal(
            task['status'], 'ready',
            "Task '{name}' has incorrect status. {} != {}".format(
                task['status'], 'ready', name=task["name"]
            )
        )

    @logwrap
    def assert_task_failed(self, task, timeout=70 * 60, interval=5):
        task = self.task_wait(task, timeout, interval)
        assert_equal(
            'error', task['status'],
            "Task '{name}' has incorrect status. {} != {}".format(
                task['status'], 'error', name=task["name"]
            )
        )

    @logwrap
    def create_cluster(self,
                       name,
                       settings=None,
                       release_name=help_data.OPENSTACK_RELEASE,
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
        #TODO back
        release_id = self.client.get_release_id(release_name=release_name)
        logging.info('Release_id is %s' % str(release_id))

        if settings is None:
            settings = {}

        logging.info('I pass if with settings')

        cluster_id = self.client.get_cluster_id(name)
        if not cluster_id:
            logging.info('I have no id')
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

            attributes['editable']['common']['debug']['value'] = True
            self.client.update_cluster_attributes(cluster_id, attributes)
            self.update_network_configuration(cluster_id)

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
        try:
            wait(
                lambda: self.client.get_task(
                    task['id'])['status'] != 'running',
                interval=interval,
                timeout=timeout
            )
        except TimeoutError:
            raise TimeoutError(
                "Waiting task \"{task}\" timeout {timeout} sec "
                "was exceeded: ".format(task=task["name"], timeout=timeout))

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

        self.update_nodes_interfaces(cluster_id)

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
            self, license_type=help_data.REDHAT_LICENSE_TYPE,
            username=help_data.REDHAT_USERNAME, password=help_data.REDHAT_PASSWORD,
            satellite_host=help_data.REDHAT_SATELLITE_HOST,
            activation_key=help_data.REDHAT_ACTIVATION_KEY):

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
            net_manager=help_data.NETWORK_MANAGERS['vlan'])

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

    @logwrap
    def update_nodes_interfaces(self, cluster_id):
        cluster = self.client.get_cluster(cluster_id)
        net_provider = self.client.get_cluster(cluster_id)['net_provider']
        if NEUTRON == net_provider:
            assigned_networks = {
                    'eth1': ['public'],
                    'eth2': ['management'],
                    'eth4': ['storage'],
            }

            if cluster['net_segment_type'] == NEUTRON_SEGMENT['vlan']:
                assigned_networks.update({'eth3': ['private']})
        else:
            assigned_networks = {
                'eth1': ['floating', 'public'],
                'eth2': ['management'],
                'eth3': ['fixed'],
                'eth4': ['storage'],
            }

        nailgun_nodes = self.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
             self.update_node_networks(node['id'], assigned_networks)

    @logwrap
    def update_network_configuration(self, cluster_id):
        net_config = self.client.get_networks(cluster_id)
        net_provider = self.client.get_cluster(cluster_id)['net_provider']

        self.client.update_network(cluster_id=cluster_id,
                                   networks=self.update_net_settings(net_config,
                                                                     net_provider),
                                   all_set=True)

    def update_net_settings(self, network_configuration, net_provider):
        for net in network_configuration.get('networks'):
            self.set_network(net_config=net,
                             net_name=net['name'])

        if NEUTRON == net_provider:
            neutron_params = network_configuration['neutron_parameters']['predefined_networks']['net04_ext']['L3']
            neutron_params['cidr'] = self.environment.get_network('public')
            neutron_params['gateway'] = self.environment.router('public')
            neutron_params['floating'] = self.get_range(self.environment.get_network('public'), 1)[0]

        print network_configuration
        return network_configuration

    def set_network(self, net_config, net_name):
        if 'floating' == net_name:
            self.net_settings(net_config, 'public', True)
        elif net_name in ['management', 'storage', 'public']:
            self.net_settings(net_config, net_name)

    def net_settings(self, net_config, net_name, floating=False):
        ip_network = IPNetwork(self.environment.get_network(net_name))
        if 'nova_network':
            net_config['ip_ranges'] = self.get_range(ip_network, 1) \
                if floating else self.get_range(ip_network, -1)
        else:
            net_config['ip_ranges'] = self.get_range(ip_network)

        net_config['network_size'] = len(list(ip_network))
        net_config['netmask'] = self.environment.get_net_mask(net_name)
        net_config['vlan_start'] = None
        net_config['cidr'] = str(ip_network)
        net_config['gateway'] = self.environment.router(net_name) #if net_name != "nat" else None

    def get_range(self, ip_network, ip_range=0):
        net = list(IPNetwork(ip_network))
        half = len(net)/2
        if ip_range == 0:
            return [[str(net[2]), str(net[-2])]]
        elif ip_range == 1:
            return [[str(net[half]), str(net[-2])]]
        elif ip_range == -1:
            return [[str(net[2]), str(net[half - 1])]]