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
import time
import traceback
import yaml

from devops.error import DevopsCalledProcessError
from devops.error import TimeoutError
from devops.helpers.helpers import _wait
from devops.helpers.helpers import wait
from netaddr import IPNetwork
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_true

from fuelweb_test.helpers import checkers
from fuelweb_test import logwrap
from fuelweb_test import logger
from fuelweb_test.helpers.decorators import custom_repo
from fuelweb_test.helpers.decorators import update_ostf
from fuelweb_test.helpers.decorators import upload_manifests
from fuelweb_test.helpers.security import SecurityChecks
from fuelweb_test.models.nailgun_client import NailgunClient
from fuelweb_test import ostf_test_mapping as map_ostf
from fuelweb_test.settings import ATTEMPTS
from fuelweb_test.settings import BONDING
from fuelweb_test.settings import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.settings import KVM_USE
from fuelweb_test.settings import MULTIPLE_NETWORKS
from fuelweb_test.settings import NEUTRON
from fuelweb_test.settings import NEUTRON_SEGMENT
from fuelweb_test.settings import NODEGROUPS
from fuelweb_test.settings import OPENSTACK_RELEASE
from fuelweb_test.settings import OPENSTACK_RELEASE_UBUNTU
from fuelweb_test.settings import OSTF_TEST_NAME
from fuelweb_test.settings import OSTF_TEST_RETRIES_COUNT
from fuelweb_test.settings import TIMEOUT

import fuelweb_test.settings as help_data


class FuelWebClient(object):

    def __init__(self, admin_node_ip, environment):
        self.admin_node_ip = admin_node_ip
        self.client = NailgunClient(admin_node_ip)
        self._environment = environment
        self.security = SecurityChecks(self.client, self._environment)
        super(FuelWebClient, self).__init__()

    @property
    def environment(self):
        """Environment Model
        :rtype: EnvironmentModel
        """
        return self._environment

    @staticmethod
    @logwrap
    def get_cluster_status(os_conn, smiles_count, networks_count=1):
        checkers.verify_service_list_api(os_conn, service_count=smiles_count)
        checkers.verify_glance_image_api(os_conn)
        checkers.verify_network_list_api(os_conn, networks_count)

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
    def assert_cluster_ready(self, os_conn, smiles_count,
                             networks_count=1, timeout=300):
        logger.info('Assert cluster services are UP')
        _wait(
            lambda: self.get_cluster_status(
                os_conn,
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
        fail_details = []

        for set_result in set_result_list:
            for test in set_result['tests']:
                intresting_test = False

                for test_class in tests_must_be_passed:
                    if test['id'].find(test_class) > -1:
                        intresting_test = True

                if intresting_test:
                    if test['status'] == 'success':
                        tests_pass_count += 1
                        logger.info('Passed OSTF tests %s found', test_class)
                    else:
                        details = ('%s (%s). Test status: %s, message: %s'
                                   % (test['name'], test['id'], test['status'],
                                      test['message']))
                        fail_details.append(details)

        assert_true(tests_pass_count == tests_count,
                    'The following tests have not succeeded, while they '
                    'must have passed: %s' % fail_details)

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
             for test in set_result['tests']
             if test['status'] not in ['success', 'disabled', 'skipped']]

            [test_result.update({test['name']:test['status']})
             for test in set_result['tests']]

            [failed_tests_res.append(
                {'%s (%s)' % (test['name'], test['status']): test['message']})
             for test in set_result['tests']
             if test['status'] not in ['success', 'disabled', 'skipped']]

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
            if release["name"].lower().find(release_name) != -1:
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
    def assert_fuel_version(self, fuel_version):
        logger.info('Assert fuel version is {0}'.format(fuel_version))
        version = self.client.get_api_version()
        logger.debug('version get from api is {0}'.format(version['release']))
        assert_equal(version['release'], fuel_version,
                     'Release state is not {0}'.format(fuel_version))

    @logwrap
    def assert_nailgun_upgrade_migration(self,
                                         key='can_update_from_versions'):
        for release in self.client.get_releases():
            assert_true(key in release)

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
    def get_pcm_nodes(self, ctrl_node, pure=False):
        nodes = {}
        remote = self.get_ssh_for_node(ctrl_node)
        pcs_status = remote.execute('pcs status nodes')['stdout']
        pcm_nodes = yaml.load(''.join(pcs_status).strip())
        for status in ('Online', 'Offline', 'Standby'):
            list_nodes = (pcm_nodes['Pacemaker Nodes'][status] or '').split()
            if not pure:
                nodes[status] = [self.get_fqdn_by_hostname(x)
                                 for x in list_nodes]
            else:
                nodes[status] = list_nodes
        return nodes

    @logwrap
    def assert_pacemaker(self, ctrl_node, online_nodes, offline_nodes):
        logger.info('Assert pacemaker status at devops node %s', ctrl_node)
        fqdn_names = lambda nodes: sorted([self.fqdn(n) for n in nodes])

        online = fqdn_names(online_nodes)
        offline = fqdn_names(offline_nodes)
        try:
            wait(lambda: self.get_pcm_nodes(ctrl_node)['Online'] == online and
                 self.get_pcm_nodes(ctrl_node)['Offline'] == offline,
                 timeout=60)
        except TimeoutError:
            nodes = self.get_pcm_nodes(ctrl_node)
            assert_true(nodes['Online'] == online,
                        'Online nodes: {0} ; should be online: {1}'
                        .format(nodes['Online'], online))
            assert_true(nodes['Offline'] == offline,
                        'Offline nodes: {0} ; should be offline: {1}'
                        .format(nodes['Offline'], offline))

    @logwrap
    @upload_manifests
    @update_ostf
    def create_cluster(self,
                       name,
                       settings=None,
                       release_name=help_data.OPENSTACK_RELEASE,
                       mode=DEPLOYMENT_MODE_SIMPLE,
                       port=514,
                       release_id=None):
        """Creates a cluster
        :param name:
        :param release_name:
        :param mode:
        :param settings:
        :param port:
        :return: cluster_id
        """
        logger.info('Create cluster with name %s', name)
        if not release_id:
            release_id = self.client.get_release_id(release_name=release_name)
            logger.info('Release_id of %s is %s',
                        release_name, str(release_id))

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
                        'net_segment_type': settings["net_segment_type"],
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
                              'objects_ceph', 'osd_pool_size', 'volumes_lvm',
                              'volumes_vmdk', 'images_vcenter'):
                    section = 'storage'
                if option in ('tenant', 'password', 'user'):
                    section = 'access'
                if option in ('vc_password', 'cluster', 'host_ip', 'vc_user'):
                    section = 'vcenter'
                if option == 'assign_to_all_nodes':
                    section = 'public_network_assignment'
                if section:
                    attributes['editable'][section][option]['value'] =\
                        settings[option]
            if help_data.IMAGE_PROVISIONING:
                attributes['editable']['provision']['method']['value'] = \
                    'image'

            logger.info('Set DEBUG MODE to %s', help_data.DEBUG_MODE)
            attributes['editable']['common']['debug']['value'] = \
                help_data.DEBUG_MODE

            if KVM_USE:
                logger.info('Set Hypervisor type to KVM')
                hpv_data = attributes['editable']['common']['libvirt_type']
                hpv_data['value'] = "kvm"

            if help_data.VCENTER_USE:
                logger.info('Set Hypervisor type to vCenter')
                hpv_data = attributes['editable']['common']['libvirt_type']
                hpv_data['value'] = "vcenter"

                datacenter = attributes['editable']['storage']['vc_datacenter']
                datacenter['value'] = help_data.VC_DATACENTER

                datastore = attributes['editable']['storage']['vc_datastore']
                datastore['value'] = help_data.VC_DATASTORE

                imagedir = attributes['editable']['storage']['vc_image_dir']
                imagedir['value'] = help_data.VC_IMAGE_DIR

                host = attributes['editable']['storage']['vc_host']
                host['value'] = help_data.VC_HOST

                vc_user = attributes['editable']['storage']['vc_user']
                vc_user['value'] = help_data.VC_USER

                vc_password = attributes['editable']['storage']['vc_password']
                vc_password['value'] = help_data.VC_PASSWORD

                vc_clusters = attributes['editable']['vcenter']['cluster']
                vc_clusters['value'] = help_data.VCENTER_CLUSTERS

            logger.debug("Try to update cluster "
                         "with next attributes {0}".format(attributes))
            self.client.update_cluster_attributes(cluster_id, attributes)

            logger.debug("Attributes of cluster were updated,"
                         " going to update networks ...")
            if MULTIPLE_NETWORKS:
                node_groups = {n['name']: [] for n in NODEGROUPS}
                self.update_nodegroups(cluster_id, node_groups)
                for NODEGROUP in NODEGROUPS:
                    self.update_network_configuration(cluster_id,
                                                      nodegroup=NODEGROUP)
            else:
                self.update_network_configuration(cluster_id)

        if not cluster_id:
            raise Exception("Could not get cluster '%s'" % name)
        # TODO: rw105719
        # self.client.add_syslog_server(
        #    cluster_id, self.environment.get_host_node_ip(), port)

        return cluster_id

    @custom_repo
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
        return ''.join(remote.check_call('crm_resource --list')['stdout'])

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
                get_node(name=node_name)
            node = self.get_nailgun_node_by_devops_node(slave)
            nailgun_node_roles.append((node, nodes_dict[node_name]))
        return nailgun_node_roles

    @logwrap
    def get_nailgun_node_by_name(self, node_name):
        logger.info('Get nailgun node by %s devops node', node_name)
        return self.get_nailgun_node_by_devops_node(
            self.environment.get_virtual_environment().get_node(
                name=node_name))

    @logwrap
    def get_nailgun_node_by_devops_node(self, devops_node):
        """Return slave node description.
        Returns dict with nailgun slave node description if node is
        registered. Otherwise return None.
        """
        d_macs = {i.mac_address.upper() for i in devops_node.interfaces}
        logger.debug('Verify that nailgun api is running')
        attempts = ATTEMPTS
        while attempts > 0:
            logger.debug(
                'current timeouts is {0} count of '
                'attempts is {1}'.format(TIMEOUT, attempts))
            try:
                self.client.list_nodes()
                attempts = 0
            except Exception:
                logger.debug(traceback.format_exc())
                attempts -= 1
                time.sleep(TIMEOUT)
        logger.debug('Look for nailgun node by macs %s', d_macs)
        for nailgun_node in self.client.list_nodes():
            macs = {i['mac'] for i in nailgun_node['meta']['interfaces']}
            logger.debug('Look for macs returned by nailgun {0}'.format(macs))
            # Because our HAproxy may create some interfaces
            if d_macs.issubset(macs):
                nailgun_node['devops_name'] = devops_node.name
                return nailgun_node
        return None

    @logwrap
    def find_devops_node_by_nailgun_fqdn(self, fqdn, devops_nodes):
        def get_nailgun_node(fqdn):
            for nailgun_node in self.client.list_nodes():
                if nailgun_node['meta']['system']['fqdn'] == fqdn:
                    return nailgun_node

        nailgun_node = get_nailgun_node(fqdn)
        macs = {i['mac'] for i in nailgun_node['meta']['interfaces']}
        for devops_node in devops_nodes:
            devops_macs = {i.mac_address.upper()
                           for i in devops_node.interfaces}
            if devops_macs == macs:
                return devops_node

    @logwrap
    def get_ssh_for_node(self, node_name):
        ip = self.get_nailgun_node_by_devops_node(
            self.environment.get_virtual_environment().
            get_node(name=node_name))['ip']
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
        return self.client.verify_networks(cluster_id)

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
                             test_sets=None, test_name=None,
                             retries=None, timeout=15 * 60):
        self.client.ostf_run_singe_test(cluster_id, test_sets, test_name)
        if retries:
            return self.return_ostf_results(cluster_id, timeout=timeout)
        else:
            self.assert_ostf_run_certain(cluster_id,
                                         tests_must_be_passed=[test_name],
                                         timeout=timeout)

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
                     pending_addition=True, pending_deletion=False,
                     update_nodegroups=False):
        # update nodes in cluster
        nodes_data = []
        nodes_groups = {}
        for node_name in nodes_dict:
            if MULTIPLE_NETWORKS:
                node_roles = nodes_dict[node_name][0]
                node_group = nodes_dict[node_name][1]
            else:
                node_roles = nodes_dict[node_name]
                node_group = 'default'

            devops_node = self.environment.get_virtual_environment().\
                get_node(name=node_name)

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
                'pending_roles': node_roles,
                'name': '{}_{}'.format(node_name, "_".join(node_roles))
            }
            nodes_data.append(node_data)
            if node_group not in nodes_groups.keys():
                nodes_groups[node_group] = []
            nodes_groups[node_group].append(node)

        # assume nodes are going to be updated for one cluster only
        cluster_id = nodes_data[-1]['cluster_id']
        node_ids = [str(node_info['id']) for node_info in nodes_data]
        self.client.update_nodes(nodes_data)

        nailgun_nodes = self.client.list_cluster_nodes(cluster_id)
        cluster_node_ids = map(lambda _node: str(_node['id']), nailgun_nodes)
        assert_true(
            all([node_id in cluster_node_ids for node_id in node_ids]))

        self.update_nodes_interfaces(cluster_id)
        if update_nodegroups:
            self.update_nodegroups(nodes_groups)

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
    def get_node_disk_size(self, node_id, disk_name):
        disks = self.client.get_node_disks(node_id)
        size = 0
        for disk in disks:
            if disk['name'] == disk_name:
                for volume in disk['volumes']:
                    size += volume['size']
        return size

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
        self.client.update_network(
            cluster_id,
            networking_parameters={
                "net_manager": help_data.NETWORK_MANAGERS['vlan'],
                "fixed_network_size": network_size,
                "fixed_networks_amount": amount
            }
        )

    @logwrap
    def verify_network(self, cluster_id, timeout=60 * 5, success=True):
        # TODO(apanchenko): remove this hack when network verification begins
        # TODO(apanchenko): to work for environments with multiple net groups
        if MULTIPLE_NETWORKS:
            logger.warning('Network verification is temporary disabled when '
                           '"multiple cluster networks" feature is used')
            return
        task = self.run_network_verify(cluster_id)
        if success:
            self.assert_task_success(task, timeout, interval=10)
        else:
            self.assert_task_failed(task, timeout, interval=10)

    @logwrap
    def update_nodes_interfaces(self, cluster_id):
        net_provider = self.client.get_cluster(cluster_id)['net_provider']
        if NEUTRON == net_provider:
            assigned_networks = {
                'eth1': ['public'],
                'eth2': ['management'],
                'eth4': ['storage'],
            }

            if self.client.get_networks(cluster_id).\
                get("networking_parameters").\
                get("segmentation_type") == \
                    NEUTRON_SEGMENT['vlan']:
                assigned_networks.update({'eth3': ['private']})
        else:
            assigned_networks = {
                'eth1': ['public'],
                'eth2': ['management'],
                'eth3': ['fixed'],
                'eth4': ['storage'],
            }

        nailgun_nodes = self.client.list_cluster_nodes(cluster_id)
        for node in nailgun_nodes:
            self.update_node_networks(node['id'], assigned_networks)

    @logwrap
    def update_network_configuration(self, cluster_id, nodegroup=None):
        net_config = self.client.get_networks(cluster_id)
        if not nodegroup:
            logger.info('Update network settings of cluster %s', cluster_id)
            new_settings = self.update_net_settings(net_config)
            self.client.update_network(
                cluster_id=cluster_id,
                networking_parameters=new_settings["networking_parameters"],
                networks=new_settings["networks"]
            )
        else:
            logger.info('Update network settings of cluster %s, nodegroup %s',
                        cluster_id, nodegroup['name'])
            new_settings = self.update_net_settings(net_config, nodegroup,
                                                    cluster_id)
            self.client.update_network(
                cluster_id=cluster_id,
                networking_parameters=new_settings["networking_parameters"],
                networks=new_settings["networks"]
            )

    def update_net_settings(self, network_configuration, nodegroup=None,
                            cluster_id=None):
        if not nodegroup:
            for net in network_configuration.get('networks'):
                self.set_network(net_config=net,
                                 net_name=net['name'])

            self.common_net_settings(network_configuration)
            return network_configuration
        else:
            nodegroup_id = self.get_nodegroup(cluster_id,
                                              nodegroup['name'])['id']
            for net in network_configuration.get('networks'):
                if net['group_id'] == nodegroup_id:
                    # Do not overwrite default PXE admin network configuration
                    if nodegroup['name'] == 'default' and \
                       net['name'] == 'fuelweb_admin':
                        continue
                    self.set_network(net_config=net,
                                     net_name=net['name'],
                                     net_pools=nodegroup['pools'])

            self.common_net_settings(network_configuration)
            return network_configuration

    def common_net_settings(self, network_configuration):
        nc = network_configuration["networking_parameters"]
        public = IPNetwork(self.environment._get_network("public"))

        float_range = public if not BONDING else list(public.subnet(27))[0]
        nc["floating_ranges"] = self.get_range(float_range, 1)

    def set_network(self, net_config, net_name, net_pools=None):
        nets_wo_floating = ['public', 'management', 'storage']
        if not net_pools:
            if not BONDING:
                if 'floating' == net_name:
                    self.net_settings(net_config, 'public', floating=True)
                elif net_name in nets_wo_floating:
                    self.net_settings(net_config, net_name)
            else:
                pub_subnets = list(IPNetwork(
                    self.environment._get_network("public")).subnet(27))
                if "floating" == net_name:
                    self.net_settings(net_config, pub_subnets[0],
                                      floating=True, jbond=True)
                elif net_name in nets_wo_floating:
                    i = nets_wo_floating.index(net_name)
                    self.net_settings(net_config, pub_subnets[i], jbond=True)
        else:
            def _get_true_net_name(_name):
                for _net in net_pools:
                    if _name in _net:
                        return _net

            public_net = _get_true_net_name('public')
            admin_net = _get_true_net_name('admin')

            if not BONDING:
                if 'floating' == net_name:
                    self.net_settings(net_config, public_net, floating=True)
                elif net_name in nets_wo_floating:
                    self.net_settings(net_config, _get_true_net_name(net_name))
                elif net_name in 'fuelweb_admin':
                    self.net_settings(net_config, admin_net)
            else:
                pub_subnets = list(IPNetwork(
                    self.environment._get_network(public_net)).subnet(27))

                if "floating" == net_name:
                    self.net_settings(net_config, pub_subnets[0],
                                      floating=True, jbond=True)
                elif net_name in nets_wo_floating:
                    i = nets_wo_floating.index(net_name)
                    self.net_settings(net_config, pub_subnets[i], jbond=True)
                elif net_name in 'fuelweb_admin':
                    self.net_settings(net_config, admin_net)

    def net_settings(self, net_config, net_name, floating=False, jbond=False):
        if jbond:
            ip_network = net_name
        else:
            ip_network = IPNetwork(self.environment._get_network(net_name))
            if 'admin' in net_name:
                net_config['ip_ranges'] = self.get_range(ip_network, 2)

        net_config['ip_ranges'] = self.get_range(ip_network, 1) \
            if floating else self.get_range(ip_network, -1)

        net_config['cidr'] = str(ip_network)

        if jbond:
            if net_config['name'] == 'public':
                net_config['gateway'] = \
                    self.environment.get_virtual_environment().router('public')
        else:
            net_config['vlan_start'] = None
            net_config['gateway'] = self.environment.get_virtual_environment(
            ).router(net_name)

    def get_range(self, ip_network, ip_range=0):
        net = list(IPNetwork(ip_network))
        half = len(net) / 2
        if ip_range == 0:
            return [[str(net[2]), str(net[-2])]]
        elif ip_range == 1:
            return [[str(net[half]), str(net[-2])]]
        elif ip_range == -1:
            return [[str(net[2]), str(net[half - 1])]]
        elif ip_range == 2:
            return [[str(net[3]), str(net[half - 1])]]

    def get_floating_ranges(self, network_set=''):
        net_name = 'public{0}'.format(network_set)
        net = list(IPNetwork(self.environment._get_network(net_name)))
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
                    'online'], timeout=60 * 10)
            logger.info('Start %s node', node.name)
            node.destroy()
            node.create()

        for node in devops_nodes:
            wait(
                lambda: self.get_nailgun_node_by_devops_node(node)['online'],
                timeout=60 * 10)

    def cold_restart_nodes(self, devops_nodes):
        logger.info('Cold restart nodes %s',
                    [n.name for n in devops_nodes])
        for node in devops_nodes:
            logger.info('Destroy node %s', node.name)
            node.destroy()
        for node in devops_nodes:
            logger.info('Wait a %s node offline status', node.name)
            wait(lambda: not self.get_nailgun_node_by_devops_node(
                 node)['online'], timeout=60 * 10)
            logger.info('Start %s node', node.name)
            node.create()
        for node in devops_nodes:
            wait(
                lambda: self.get_nailgun_node_by_devops_node(node)['online'],
                timeout=60 * 10)
            remote = self.environment.get_ssh_to_remote_by_name(node.name)
            try:
                self.environment.sync_node_time(remote)
            except Exception as e:
                logger.warning(
                    'Exception caught while trying to sync time on {0}:'
                    ' {1}'.format(node.name, e))

    @logwrap
    def ip_address_show(self, node_name, namespace, interface):
        try:
            remote = self.get_ssh_for_node(node_name)
            ret = remote.check_call(
                'ip netns exec {0} ip -4 -o address show {1}'.format(
                    namespace, interface))
            return ' '.join(ret['stdout'])
        except DevopsCalledProcessError as err:
            logger.error(err)
        return ''

    @logwrap
    def ip_address_del(self, node_name, namespace, interface, ip):
        logger.info('Delete %s ip address of %s interface at %s node',
                    ip, interface, node_name)
        remote = self.get_ssh_for_node(node_name)
        remote.check_call(
            'ip netns exec {0} ip addr'
            ' del {1} dev {2}'.format(namespace, ip, interface))

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

    @logwrap
    def wait_mysql_galera_is_up(self, node_names):
        def _get_galera_status(_remote):
            cmd = ("mysql --connect_timeout=5 -sse \"SELECT VARIABLE_VALUE "
                   "FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME"
                   " = 'wsrep_ready';\"")
            result = _remote.execute(cmd)
            if result['exit_code'] == 0:
                return ''.join(result['stdout']).strip()
            else:
                return ''.join(result['stderr']).strip()

        for node_name in node_names:
            remote = self.environment.get_ssh_to_remote_by_name(node_name)
            try:
                wait(lambda: _get_galera_status(remote) == 'ON',
                     timeout=30 * 4)
                logger.info("MySQL Galera is up on {host} node.".format(
                            host=node_name))
            except TimeoutError:
                logger.error("MySQL Galera isn't ready on {0}: {1}"
                             .format(node_name, _get_galera_status(remote)))
                raise TimeoutError("MySQL Galera is down")
        return True

    @logwrap
    def wait_cinder_is_up(self, node_names):
        logger.info("Waiting for all Cinder services up.")
        for node_name in node_names:
            remote = self.environment.get_ssh_to_remote_by_name(node_name)
            try:
                wait(lambda: checkers.check_cinder_status(remote),
                     timeout=300)
                logger.info("All Cinder services up.")
            except TimeoutError:
                logger.error("Cinder services not ready.")
                raise TimeoutError("Cinder services not ready.")
        return True

    def run_ostf_repeatably(self, cluster_id, test_name=None,
                            test_retries=None, checks=None):
        res = []
        passed_count = []
        failed_count = []
        test_nama_to_ran = test_name or OSTF_TEST_NAME
        retr = test_retries or OSTF_TEST_RETRIES_COUNT
        test_path = map_ostf.OSTF_TEST_MAPPING.get(test_nama_to_ran)
        logger.info('Test path is {0}'.format(test_path))

        for i in range(0, retr):
            result = self.run_single_ostf_test(
                cluster_id=cluster_id, test_sets=['smoke', 'sanity'],
                test_name=test_path,
                retries=True)
            res.append(result)
            logger.info('res is {0}'.format(res))

        logger.info('full res is {0}'.format(res))
        for element in res:
            [passed_count.append(test)
             for test in element if test.get(test_name) == 'success']
            [failed_count.append(test)
             for test in element if test.get(test_name) == 'failure']
            [failed_count.append(test)
             for test in element if test.get(test_name) == 'error']

        if not checks:
            assert_true(
                len(passed_count) == test_retries,
                'not all retries were successful,'
                ' fail {0} retries'.format(len(failed_count)))
        else:
            return failed_count

    def get_nailgun_version(self):
        logger.info("ISO version: %s" % self.client.get_api_version())

    @logwrap
    def sync_ceph_time(self, ceph_nodes):
        self.environment.sync_time_admin_node()
        if OPENSTACK_RELEASE_UBUNTU in OPENSTACK_RELEASE:
            cmd = 'service ceph-all restart'
        else:
            cmd = 'service ceph restart'
        for node in ceph_nodes:
            remote = self.environment.get_ssh_to_remote(node['ip'])
            self.environment.sync_node_time(remote)
            result = remote.execute(cmd)
            if not result['exit_code'] == 0:
                raise Exception('Ceph restart failed on {0}: {1}'.
                                format(node['name'], result['stderr']))

    @logwrap
    def check_ceph_status(self, cluster_id, offline_nodes=[],
                          recovery_timeout=360):
        cluster_nodes = self.client.list_cluster_nodes(cluster_id)
        ceph_nodes = [n for n in cluster_nodes if 'ceph-osd' in
                      n['roles'] and n['id'] not in offline_nodes]
        clock_skew_status = ['clock', 'skew', 'detected']
        osd_recovery_status = ['degraded', 'recovery', 'osds', 'are', 'down']

        logger.info('Waiting until Ceph service become up...')
        for node in ceph_nodes:
            remote = self.environment.get_ssh_to_remote(node['ip'])
            try:
                wait(lambda: checkers.check_ceph_ready(remote) is True,
                     interval=20, timeout=600)
            except TimeoutError:
                logger.error('Ceph service is down on {0}'.format(
                    node['name']))
                raise

        logger.info('Ceph service is ready')
        logger.info('Checking Ceph Health...')
        for node in ceph_nodes:
            remote = self.environment.get_ssh_to_remote(node['ip'])
            health_status = checkers.get_ceph_health(remote)
            if 'HEALTH_OK' in health_status:
                continue
            elif 'HEALTH_WARN' in health_status:
                if checkers.check_ceph_health(remote, clock_skew_status):
                    logger.warning('Clock skew detected in Ceph.')
                    self.sync_ceph_time(ceph_nodes)
                    try:
                        wait(lambda: checkers.check_ceph_health(remote),
                             interval=30, timeout=recovery_timeout)
                    except TimeoutError:
                        logger.error('Ceph HEALTH is bad on {0}'.format(
                            node['name']))
                        raise
                elif checkers.check_ceph_health(remote, osd_recovery_status)\
                        and len(offline_nodes) > 0:
                    logger.info('Ceph is being recovered after osd node(s)'
                                ' shutdown.')
                    try:
                        wait(lambda: checkers.check_ceph_health(remote),
                             interval=30, timeout=recovery_timeout)
                    except TimeoutError:
                        logger.error('Ceph HEALTH is bad on {0}'.format(
                            node['name']))
                        raise
            else:
                assert_true(checkers.check_ceph_health(remote),
                            'Ceph health doesn\'t equal to "OK", please '
                            'inspect debug logs for details')

        logger.info('Checking Ceph OSD Tree...')
        for node in ceph_nodes:
            remote = self.environment.get_ssh_to_remote(node['ip'])
            checkers.check_ceph_disks(remote, [n['id'] for n in ceph_nodes])
        logger.info('Ceph cluster status is OK')

    @logwrap
    def get_releases_list_for_os(self, release_name, release_version=None):
        full_list = self.client.get_releases()
        release_ids = []
        for release in full_list:
            if release_version:
                if release_name in release['name'].lower() \
                        and release_version == release['version']:
                    logger.debug('release data is {0}'.format(release))
                    release_ids.append(release['id'])
            else:
                if release_name in release['name'].lower():
                    release_ids.append(release['id'])
        return release_ids

    @logwrap
    def update_cluster(self, cluster_id, data):
        logger.debug(
            "Try to update cluster with data {0}".format(data))
        self.client.update_cluster(cluster_id, data)

    @logwrap
    def run_update(self, cluster_id, timeout, interval):
        logger.info("Run update..")
        task = self.client.run_update(cluster_id)
        logger.debug("Invocation of update runs with result {0}".format(task))
        self.assert_task_success(task, timeout=timeout, interval=interval)

    @logwrap
    def get_cluster_release_id(self, cluster_id):
        data = self.client.get_cluster(cluster_id)
        return data['release_id']

    def assert_nodes_in_ready_state(self, cluster_id):
        for nailgun_node in self.client.list_cluster_nodes(cluster_id):
            assert_equal(nailgun_node['status'], 'ready',
                         'Nailgun node status is not ready but {0}'.format(
                             nailgun_node['status']))

    @logwrap
    def manual_rollback(self, remote, rollback_version):
        remote.execute('rm /etc/supervisord.d/current')
        remote.execute('ln -s /etc/supervisord.d/{0}/ '
                       '/etc/supervisord.d/current'.format(rollback_version))
        remote.execute('rm /etc/fuel/version.yaml')
        remote.execute('ln -s /etc/fuel/{0}/version.yaml '
                       '/etc/fuel/version.yaml'.format(rollback_version))
        remote.execute('rm /var/www/nailgun/bootstrap')
        remote.execute('ln -s /var/www/nailgun/{}_bootstrap '
                       '/var/www/nailgun/bootstrap'.format(rollback_version))
        logger.debug('stopping supervisor')
        try:
            remote.execute('/etc/init.d/supervisord stop')
        except Exception as e:
            logger.debug('exception is {0}'.format(e))
        logger.debug('stop docker')
        try:
            remote.execute('docker stop $(docker ps -q)')
        except Exception as e:
            logger.debug('exception is {0}'.format(e))
        logger.debug('start supervisor')
        time.sleep(60)
        try:
            remote.execute('/etc/init.d/supervisord start')
        except Exception as e:
            logger.debug('exception is {0}'.format(e))
        time.sleep(60)

    @logwrap
    def modify_python_file(self, remote, modification, file):
        remote.execute('sed -i "{0}" {1}'.format(modification, file))

    def backup_master(self, remote):
        logger.info("Backup master node")
        try:
            remote.execute("echo CALC_MY_MD5SUM > /etc/fuel/data")
            remote.execute("iptables-save > /etc/fuel/iptables-backup")
            remote.execute("md5sum /etc/fuel/data | sed -n 1p "
                           "| awk '{print $1}'>/etc/fuel/sum")
            remote.execute('dockerctl backup')
            remote.execute('rm -f /etc/fuel/data')
        except Exception:
            logger.error(traceback.format_exc())
            raise

    @logwrap
    def restore_master(self, remote):
        logger.info("Restore master node")
        path = checkers.find_backup(remote)
        try:
            remote.execute('dockerctl restore {0}'.format(path))
        except Exception:
            logger.error(traceback.format_exc())
            raise

    @logwrap
    def restore_check_nailgun_api(self, remote):
        logger.info("Restore check nailgun api")
        info = self.client.get_api_version()
        build_number = info["build_number"]
        assert_true(build_number, 'api version returned empty data')

    @logwrap
    def check_fixed_network_cidr(self, cluster_id, remote):
        net_provider = self.client.get_cluster(cluster_id)['net_provider']
        if net_provider == 'nova_network':
            nailgun_cidr = self.client.get_networks(cluster_id).\
                get("networking_parameters").get("fixed_networks_cidr")
            logger.debug('nailgun cidr is {0}'.format(nailgun_cidr))
            slave_cidr = ''.join(remote.execute(". openrc; nova net-list"
                                                " | awk '$4 =="
                                                " \"novanetwork\"{print $6}'"
                                                )['stdout'])
            logger.debug('slave cidr is {0}'.format(
                slave_cidr.rstrip()))
            assert_equal(nailgun_cidr, slave_cidr.rstrip(),
                         'Cidr after deployment is not equal'
                         ' to cidr by default')
        elif net_provider == 'neutron':
            nailgun_cidr = self.client.get_networks(cluster_id).\
                get("networking_parameters").get("internal_cidr")
            logger.debug('nailgun cidr is {0}'.format(nailgun_cidr))
            slave_cidr = ''.join(remote.execute(". openrc; neutron"
                                                " subnet-list | awk '$4 =="
                                                " \"net04__subnet\""
                                                "{print $6}'")['stdout'])
            logger.debug('slave cidr is {0}'.format(
                slave_cidr.rstrip()))
            assert_equal(nailgun_cidr, slave_cidr.rstrip(),
                         'Cidr after deployment is not equal'
                         ' to cidr by default')

    def update_internal_network(self, cluster_id, cidr, gateway=None):
        net_provider = self.client.get_cluster(cluster_id)['net_provider']
        net_config = self.client.get_networks(cluster_id)
        data = (cluster_id, net_config["networking_parameters"],
                net_config["networks"])
        if net_provider == 'nova_network':
            net_config["networking_parameters"]['fixed_networks_cidr']\
                = cidr
            self.client.update_network(*data)
        elif net_provider == 'neutron':
            net_config["networking_parameters"]['internal_cidr']\
                = cidr
            net_config["networking_parameters"]['internal_gateway']\
                = gateway
            self.client.update_network(*data)

    def get_public_vip(self, cluster_id):
        return self.client.get_networks(cluster_id)['public_vip']

    @logwrap
    def get_controller_with_running_service(self, slave, service_name):
        ret = self.get_pacemaker_status(slave.name)
        logger.debug("pacemaker status is {0}".format(ret))
        fqdn = re.search(service_name, ret).group(1)
        logger.debug('fdqn is {0}'.format(fqdn))
        devops_node = self.find_devops_node_by_nailgun_fqdn(
            fqdn, self.environment.get_virtual_environment().nodes().slaves)
        return devops_node

    @logwrap
    def get_fqdn_by_hostname(self, hostname):
        if self.environment.get_virtual_environment().domain not in hostname:
            hostname += "." + self.environment.get_virtual_environment().domain
            return hostname
        else:
            return hostname

    def get_nodegroup(self, cluster_id, name='default', group_id=None):
        ngroups = self.client.get_nodegroups()
        for group in ngroups:
            if group['cluster'] == cluster_id and group['name'] == name:
                if group_id and group['id'] != group_id:
                    continue
                return group
        return None

    def update_nodegroups(self, cluster_id, node_groups):
        for ngroup in node_groups:
            if not self.get_nodegroup(cluster_id, name=ngroup):
                self.client.create_nodegroup(cluster_id, ngroup)
            # Assign nodes to nodegroup if nodes are specified
            if len(node_groups[ngroup]) > 0:
                ngroup_id = self.get_nodegroup(cluster_id, name=ngroup)['id']
                self.client.assign_nodegroup(ngroup_id, node_groups[ngroup])
