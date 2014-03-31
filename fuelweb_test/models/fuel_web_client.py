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

import re

from devops.error import DevopsCalledProcessError
from devops.error import TimeoutError
from devops.helpers.helpers import _wait
from devops.helpers.helpers import wait
from ipaddr import IPNetwork
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_true

from fuelweb_test.helpers import checkers
from fuelweb_test import logwrap
from fuelweb_test import logger
from fuelweb_test.helpers.decorators import upload_manifests
from fuelweb_test.models.nailgun_client import NailgunClient
from fuelweb_test.settings import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.settings import KVM_USE
from fuelweb_test.settings import NEUTRON
from fuelweb_test.settings import NEUTRON_SEGMENT
from fuelweb_test.settings import OPENSTACK_RELEASE
from fuelweb_test.settings import OPENSTACK_RELEASE_UBUNTU

import fuelweb_test.settings as help_data


class FuelWebClient(object):

    def __init__(self, admin_node_ip, environment):
        self.admin_node_ip = admin_node_ip
        self.client = NailgunClient(admin_node_ip)
        self._environment = environment
        super(FuelWebClient, self).__init__()

    @property
    def environment(self):
        """Environment Model
        :rtype: EnvironmentModel
        """
        return self._environment

    @staticmethod
    @logwrap
    def get_cluster_status(ssh_remote, smiles_count, networks_count=1):
        checkers.verify_service_list(ssh_remote, smiles_count)
        checkers.verify_glance_index(ssh_remote)
        checkers.verify_network_list(networks_count, ssh_remote)

    @logwrap
    def _ostf_test_wait(self, cluster_id, timeout):
        logger.info('Wait OSTF tests at cluster #%s for %s seconds',
                    cluster_id, timeout)
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
        logger.info('Add syslog server %s:%s to cluster #%s',
                    host, port, cluster_id)
        self.client.add_syslog_server(cluster_id, host, port)

    @logwrap
    def assert_cluster_floating_list(self, node_name, expected_ips):
        logger.info('Assert floating IPs at node %s. Expected %s',
                    node_name, expected_ips)
        current_ips = self.get_cluster_floating_list(node_name)
        assert_equal(set(expected_ips), set(current_ips),
                     'Current floating IPs {0}'.format(current_ips))

    @logwrap
    def assert_cluster_ready(self, node_name, smiles_count,
                             networks_count=1, timeout=300):
        logger.info('Assert cluster services are UP')
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
    def assert_ostf_run_certain(self, cluster_id, tests_must_be_passed,
                                timeout=10 * 60):
        logger.info('Assert OSTF tests are passed at cluster #%s: %s',
                    cluster_id, tests_must_be_passed)
        set_result_list = self._ostf_test_wait(cluster_id, timeout)
        tests_pass_count = 0
        tests_count = len(tests_must_be_passed)
        result = False
        for set_result in set_result_list:
            success = [test for test in set_result['tests']
                       if test['status'] == 'success']
            for test_id in success:
                for test_class in tests_must_be_passed:
                    if test_id['id'].find(test_class) > -1:
                        tests_pass_count += 1
                        logger.info('Passed OSTF tests %s found', test_class)
        if tests_pass_count == tests_count:
            result = True
        assert_true(result)

    @logwrap
    def assert_ostf_run(self, cluster_id, should_fail=0,
                        failed_test_name=None, timeout=15 * 60):
        logger.info('Assert OSTF run at cluster #%s. '
                    'Should fail %s tests named %s',
                    cluster_id, should_fail, failed_test_name)
        set_result_list = self._ostf_test_wait(cluster_id, timeout)
        failed_tests_res = []
        failed = 0
        actual_failed_names = []
        test_result = {}
        for set_result in set_result_list:

            failed += len(
                filter(
                    lambda test: test['status'] == 'failure' or
                    test['status'] == 'error',
                    set_result['tests']
                )
            )

            [actual_failed_names.append(test['name'])
             for test in set_result['tests'] if test['status'] != 'success']

            [test_result.update({test['name']:test['status']})
             for test in set_result['tests']]

            [failed_tests_res.append({test['name']:test['message']})
             for test in set_result['tests'] if test['status'] != 'success']

        logger.info('OSTF test statuses are : {0}'.format(test_result))

        if failed_test_name:
            for test_name in failed_test_name:
                assert_true(test_name in actual_failed_names,
                            'WARNINg unexpected fail,'
                            'expected {0} actual {1}'.format(
                                failed_test_name, actual_failed_names))

        assert_true(
            failed <= should_fail, 'Failed tests,  fails: {} should fail:'
                                   ' {} failed tests name: {}'
                                   ''.format(failed, should_fail,
                                             failed_tests_res))

    def assert_release_state(self, release_name, state='available'):
        logger.info('Assert release %s has state %s', release_name, state)
        for release in self.client.get_releases():
            if release["name"].find(release_name) != -1:
                assert_equal(release['state'], state,
                             'Release state {0}'.format(release['state']))
                return release["id"]

    def assert_release_role_present(self, release_name, role_name):
        logger.info('Assert role %s is available in release %s',
                    role_name, release_name)
        id = self.assert_release_state(release_name)
        release_data = self.client.get_releases_details(release_id=id)
        assert_equal(
            True, role_name in release_data['roles'],
            message='There is no {0} role in release id {1}'.format(
                role_name, release_name))

    @logwrap
    def assert_task_success(
            self, task, timeout=130 * 60, interval=5, progress=None):
        logger.info('Assert task %s is success', task)
        if not progress:
            task = self.task_wait(task, timeout, interval)
            assert_equal(
                task['status'], 'ready',
                "Task '{name}' has incorrect status. {} != {}".format(
                    task['status'], 'ready', name=task["name"]
                )
            )
        else:
            logger.info('Start to polling task progress')
            task = self.task_wait_progress(
                task, timeout=timeout, interval=interval, progress=progress)
            assert_true(
                task['progress'] >= progress,
                'Task has other progress{0}'.format(task['progress']))

    @logwrap
    def assert_task_failed(self, task, timeout=70 * 60, interval=5):
        logger.info('Assert task %s is failed', task)
        task = self.task_wait(task, timeout, interval)
        assert_equal(
            'error', task['status'],
            "Task '{name}' has incorrect status. {} != {}".format(
                task['status'], 'error', name=task["name"]
            )
        )

    @logwrap
    def fqdn(self, devops_node):
        logger.info('Get FQDN of a devops node %s', devops_node.name)
        nailgun_node = self.get_nailgun_node_by_devops_node(devops_node)
        if OPENSTACK_RELEASE_UBUNTU in OPENSTACK_RELEASE:
            return nailgun_node['meta']['system']['fqdn']
        return nailgun_node['fqdn']

    @logwrap
    def assert_pacemaker(self, ctrl_node, online_nodes, offline_nodes):
        logger.info('Assert pacemaker status at devops node %s', ctrl_node)
        fqdn_names = lambda nodes: sorted([self.fqdn(n) for n in nodes])

        # Assert online nodes list
        online = \
            'Online: [ {0} ]'.format(' '.join(fqdn_names(online_nodes)))
        wait(lambda: online in self.get_pacemaker_status(
            ctrl_node), timeout=30)
        assert_true(
            online in self.get_pacemaker_status(ctrl_node),
            'Online nodes {0}'.format(online))

        # Assert offline nodes list
        if len(offline_nodes) > 0:
            offline = \
                'OFFLINE: [ {0} ]'.format(
                    ' '.join(fqdn_names(offline_nodes)))
            wait(lambda: offline in self.get_pacemaker_status(
                ctrl_node), timeout=30)
            assert_true(
                offline in self.get_pacemaker_status(ctrl_node),
                'Offline nodes {0}'.format(offline_nodes))

    @logwrap
    @upload_manifests
    def create_cluster(self,
                       name,
                       settings=None,
                       release_name=help_data.OPENSTACK_RELEASE,
                       mode=DEPLOYMENT_MODE_SIMPLE,
                       port=5514):
        """Creates a cluster
        :param name:
        :param release_name:
        :param mode:
        :param settings:
        :param port:
        :return: cluster_id
        """
        logger.info('Create cluster with name %s', name)
        release_id = self.client.get_release_id(release_name=release_name)
        logger.info('Release_id of %s is %s', release_name, str(release_id))

        if settings is None:
            settings = {}

        cluster_id = self.client.get_cluster_id(name)
        if not cluster_id:
            logger.info('I have no id :(')
            data = {
                "name": name,
                "release": str(release_id),
                "mode": mode
            }

            if "net_provider" in settings:
                data.update(
                    {
                        'net_provider': settings["net_provider"],
                        'net_segment_type': settings[
                            "net_segment_type"]
                    }
                )

            self.client.create_cluster(data=data)
            cluster_id = self.client.get_cluster_id(name)
            logger.info('The cluster id is %s', cluster_id)

            logger.info('Set cluster settings to %s', settings)
            attributes = self.client.get_cluster_attributes(cluster_id)

            for option in settings:
                section = False
                if option in ('sahara', 'murano', 'ceilometer'):
                    section = 'additional_components'
                if option in ('volumes_ceph', 'images_ceph', 'ephemeral_ceph',
                              'objects_ceph', 'osd_pool_size', 'volumes_lvm'):
                    section = 'storage'
                if section:
                    attributes['editable'][section][option]['value'] =\
                        settings[option]

            logger.info('Set DEBUG MODE to %s', help_data.DEBUG_MODE)
            attributes['editable']['common']['debug']['value'] = \
                help_data.DEBUG_MODE

            if KVM_USE:
                logger.info('Set Hypervisor type to KVM')
                hpv_data = attributes['editable']['common']['libvirt_type']
                hpv_data['value'] = "kvm"

            self.client.update_cluster_attributes(cluster_id, attributes)
            self.update_network_configuration(cluster_id)

        if not cluster_id:
            raise Exception("Could not get cluster '%s'" % name)

        self.client.add_syslog_server(
            cluster_id, self.environment.get_host_node_ip(), port)

        return cluster_id

    def deploy_cluster_wait(self, cluster_id, is_feature=False,
                            timeout=50 * 60, interval=30):
        if not is_feature:
            logger.info('Deploy cluster %s', cluster_id)
            task = self.deploy_cluster(cluster_id)
            self.assert_task_success(task, interval=interval)
        else:
            logger.info('Provision nodes of a cluster %s', cluster_id)
            task = self.client.provision_nodes(cluster_id)
            self.assert_task_success(task, timeout=timeout, interval=interval)
            logger.info('Deploy nodes of a cluster %s', cluster_id)
            task = self.client.deploy_nodes(cluster_id)
            self.assert_task_success(task, timeout=timeout, interval=interval)

    def deploy_cluster_wait_progress(self, cluster_id, progress):
        task = self.deploy_cluster(cluster_id)
        self.assert_task_success(task, interval=30, progress=progress)

    @logwrap
    def deploy_cluster(self, cluster_id):
        """Return hash with task description."""
        logger.info('Launch deployment of a cluster #%s', cluster_id)
        return self.client.deploy_cluster_changes(cluster_id)

    @logwrap
    def get_cluster_floating_list(self, node_name):
        logger.info('Get floating IPs list at %s devops node', node_name)
        remote = self.get_ssh_for_node(node_name)
        ret = remote.check_call('/usr/bin/nova-manage floating list')
        ret_str = ''.join(ret['stdout'])
        return re.findall('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ret_str)

    @logwrap
    def get_cluster_block_devices(self, node_name):
        logger.info('Get %s node block devices (lsblk)', node_name)
        remote = self.get_ssh_for_node(node_name)
        ret = remote.check_call('/bin/lsblk')
        return ''.join(ret['stdout'])

    @logwrap
    def get_pacemaker_status(self, controller_node_name):
        logger.info('Get pacemaker status at %s node', controller_node_name)
        remote = self.get_ssh_for_node(controller_node_name)
        return ''.join(remote.check_call('crm_mon -1')['stdout'])

    @logwrap
    def get_pacemaker_config(self, controller_node_name):
        logger.info('Get pacemaker config at %s node', controller_node_name)
        remote = self.get_ssh_for_node(controller_node_name)
        return ''.join(remote.check_call('crm configure show')['stdout'])

    @logwrap
    def get_last_created_cluster(self):
        # return id of last created cluster
        logger.info('Get ID of a last created cluster')
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
        logger.info('Get nailgun node by %s devops node', node_name)
        return self.get_nailgun_node_by_devops_node(
            self.environment.get_virtual_environment().node_by_name(node_name))

    @logwrap
    def get_nailgun_node_by_devops_node(self, devops_node):
        """Return slave node description.
        Returns dict with nailgun slave node description if node is
        registered. Otherwise return None.
        """
        devops_macs = {i.mac_address.upper() for i in devops_node.interfaces}
        logger.debug('Look for nailgun node by macs %s', devops_macs)
        for nailgun_node in self.client.list_nodes():
            macs = {i['mac'] for i in nailgun_node['meta']['interfaces']}
            if devops_macs == macs:
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
        logger.info('Run network verification at cluster %s', cluster_id)
        return self.client.verify_networks(
            cluster_id, self.client.get_networks(cluster_id)['networks'])

    @logwrap
    def run_ostf(self, cluster_id, test_sets=None,
                 should_fail=0, tests_must_be_passed=None,
                 timeout=None, failed_test_name=None):
        test_sets = test_sets or ['smoke', 'sanity']
        timeout = timeout or 30 * 60
        self.client.ostf_run_tests(cluster_id, test_sets)
        if tests_must_be_passed:
            self.assert_ostf_run_certain(
                cluster_id,
                tests_must_be_passed,
                timeout)
        else:
            logger.info('Try to run assert ostf with '
                        'expected fail name {0}'.format(failed_test_name))
            self.assert_ostf_run(
                cluster_id,
                should_fail=should_fail, timeout=timeout,
                failed_test_name=failed_test_name)

    @logwrap
    def return_ostf_results(self, cluster_id, timeout):
        set_result_list = self._ostf_test_wait(cluster_id, timeout)
        tests_res = []
        for set_result in set_result_list:
            [tests_res.append({test['name']:test['status']})
             for test in set_result['tests'] if test['status'] != 'disabled']

        logger.info('OSTF test statuses are : {0}'.format(tests_res))
        return tests_res

    @logwrap
    def run_single_ostf_test(self, cluster_id,
                             test_sets=None, test_name=None, should_fail=0,
                             retries=None, timeout=15 * 60):
        self.client.ostf_run_singe_test(cluster_id, test_sets, test_name)
        if retries:
            return self.return_ostf_results(cluster_id, timeout=timeout)
        else:
            self.assert_ostf_run(cluster_id, should_fail=should_fail)

    @logwrap
    def task_wait(self, task, timeout, interval=5):
        logger.info('Wait for task %s %s seconds', task, timeout)
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
    def task_wait_progress(self, task, timeout, interval=5, progress=None):
        try:
            logger.info(
                'start to wait with timeout {0} '
                'interval {1}'.format(timeout, interval))
            wait(
                lambda: self.client.get_task(
                    task['id'])['progress'] >= progress,
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

            wait(lambda:
                 self.get_nailgun_node_by_devops_node(devops_node)['online'],
                 timeout=60 * 2)
            node = self.get_nailgun_node_by_devops_node(devops_node)
            assert_true(node['online'],
                        'Node {} is online'.format(node['mac']))

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
    def update_node_networks(self, node_id, interfaces_dict, raw_data=None):
        # fuelweb_admin is always on eth0
        interfaces_dict['eth0'] = interfaces_dict.get('eth0', [])
        if 'fuelweb_admin' not in interfaces_dict['eth0']:
            interfaces_dict['eth0'].append('fuelweb_admin')

        interfaces = self.client.get_node_interfaces(node_id)

        if raw_data:
            interfaces.append(raw_data)

        all_networks = dict()
        for interface in interfaces:
            all_networks.update(
                {net['name']: net for net in interface['assigned_networks']})

        for interface in interfaces:
            name = interface["name"]
            interface['assigned_networks'] = \
                [all_networks[i] for i in interfaces_dict.get(name, [])]

        self.client.put_node_interfaces(
            [{'id': node_id, 'interfaces': interfaces}])

    @logwrap
    def update_node_disk(self, node_id, disks_dict):
        disks = self.client.get_node_disks(node_id)
        for disk in disks:
            dname = disk['name']
            if dname not in disks_dict:
                continue
            for volume in disk['volumes']:
                vname = volume['name']
                if vname in disks_dict[dname]:
                    volume['size'] = disks_dict[dname][vname]

        self.client.put_node_disks(node_id, disks)

    @logwrap
    def update_redhat_credentials(
            self, license_type=help_data.REDHAT_LICENSE_TYPE,
            username=help_data.REDHAT_USERNAME,
            password=help_data.REDHAT_PASSWORD,
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
    def verify_network(self, cluster_id):
        task = self.run_network_verify(cluster_id)
        self.assert_task_success(task, 60 * 2, interval=10)

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
        logger.info('Update network settings of cluster %s', cluster_id)
        net_config = self.client.get_networks(cluster_id)
        net_provider = self.client.get_cluster(cluster_id)['net_provider']

        self.client.update_network(
            cluster_id=cluster_id,
            networks=self.update_net_settings(net_config, net_provider),
            all_set=True)

    def update_net_settings(self, network_configuration, net_provider):
        for net in network_configuration.get('networks'):
            self.set_network(net_config=net,
                             net_name=net['name'])

        if NEUTRON == net_provider:
            net_inf = network_configuration['neutron_parameters']
            neutron_params = net_inf['predefined_networks']['net04_ext']['L3']
            neutron_params['cidr'] = self.environment.get_network('public')
            neutron_params['gateway'] = self.environment.router('public')
            neutron_params['floating'] = self.get_range(
                self.environment.get_network('public'), 1)[0]

        logger.info('Network settings %s for push', network_configuration)
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
        net_config['gateway'] = self.environment.router(net_name)

    def get_range(self, ip_network, ip_range=0):
        net = list(IPNetwork(ip_network))
        half = len(net) / 2
        if ip_range == 0:
            return [[str(net[2]), str(net[-2])]]
        elif ip_range == 1:
            return [[str(net[half]), str(net[-2])]]
        elif ip_range == -1:
            return [[str(net[2]), str(net[half - 1])]]

    def get_floating_ranges(self):
        net = list(IPNetwork(self.environment.get_network('public')))
        ip_ranges, expected_ips = [], []

        for i in [0, -20, -40]:
            for k in range(11):
                expected_ips.append(str(net[-12 + i + k]))
            e, s = str(net[-12 + i]), str(net[-2 + i])
            ip_ranges.append([e, s])

        return ip_ranges, expected_ips

    def warm_restart_nodes(self, devops_nodes):
        logger.info('Reboot (warm restart) nodes %s',
                    [n.name for n in devops_nodes])
        for node in devops_nodes:
            logger.info('Shutdown node %s', node.name)
            remote = self.get_ssh_for_node(node.name)
            remote.check_call('/sbin/shutdown -Ph now')

        for node in devops_nodes:
            logger.info('Wait a %s node offline status', node.name)
            wait(
                lambda: not self.get_nailgun_node_by_devops_node(node)[
                    'online'])
            logger.info('Start %s node', node.name)
            node.destroy()
            node.create()

        for node in devops_nodes:
            wait(
                lambda: self.get_nailgun_node_by_devops_node(node)['online'])

    def cold_restart_nodes(self, devops_nodes):
        logger.info('Cold restart nodes %s',
                    [n.name for n in devops_nodes])
        for node in devops_nodes:
            logger.info('Destroy node %s', node.name)
            node.destroy()
        for node in devops_nodes:
            logger.info('Wait a %s node offline status', node.name)
            wait(lambda: not self.get_nailgun_node_by_devops_node(
                 node)['online'])
            logger.info('Start %s node', node.name)
            node.create()
        for node in devops_nodes:
            wait(
                lambda: self.get_nailgun_node_by_devops_node(node)['online'])

    @logwrap
    def ip_address_show(self, node_name, interface, pipe_str=''):
        try:
            remote = self.get_ssh_for_node(node_name)
            ret = remote.check_call(
                'ip address show {0} {1}'.format(interface, pipe_str))
            return ' '.join(ret['stdout'])
        except DevopsCalledProcessError as err:
            logger.error(err.message)
        return ''

    @logwrap
    def ip_address_del(self, node_name, interface, ip):
        logger.info('Delete %s ip address of %s interface at %s node',
                    ip, interface, node_name)
        remote = self.get_ssh_for_node(node_name)
        remote.check_call(
            'ip addr del {0} dev {1}'.format(ip, interface))

    @logwrap
    def provisioning_cluster_wait(self, cluster_id, progress=None):
        logger.info('Start cluster #%s provisioning', cluster_id)
        task = self.client.provision_nodes(cluster_id)
        self.assert_task_success(task, progress=progress)

    @logwrap
    def deploy_task_wait(self, cluster_id, progress):
        logger.info('Start cluster #%s deployment', cluster_id)
        task = self.client.deploy_nodes(cluster_id)
        self.assert_task_success(
            task, progress=progress)

    @logwrap
    def stop_deployment_wait(self, cluster_id):
        logger.info('Stop cluster #%s deployment', cluster_id)
        task = self.client.stop_deployment(cluster_id)
        self.assert_task_success(task, timeout=50 * 60, interval=30)

    @logwrap
    def stop_reset_env_wait(self, cluster_id):
        logger.info('Reset cluster #%s', cluster_id)
        task = self.client.reset_environment(cluster_id)
        self.assert_task_success(task, timeout=50 * 60, interval=30)

    @logwrap
    def wait_nodes_get_online_state(self, nodes):
        for node in nodes:
            logger.info('Wait for %s node online status', node.name)
            wait(lambda:
                 self.get_nailgun_node_by_devops_node(node)['online'],
                 timeout=60 * 4)
            node = self.get_nailgun_node_by_devops_node(node)
            assert_true(node['online'],
                        'Node {0} is online'.format(node['mac']))
