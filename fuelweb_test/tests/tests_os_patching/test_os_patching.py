#    Copyright 2014 Mirantis, Inc.
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

import json
import os
from proboscis.asserts import assert_not_equal
from proboscis.asserts import assert_true
from proboscis import factory
from proboscis import SkipTest
from proboscis import test

from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import packages_fixture
from fuelweb_test.helpers import utils
from fuelweb_test import settings as hlp_data
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger


@test(groups=["os_patching"])
class TestPatch(TestBasic):
    def __init__(self, snapshot):
        super(TestPatch, self).__init__()
        self.snapshot = snapshot

    @test
    @log_snapshot_on_error
    def deploy_and_patch(self):
        """Update OS on reverted env

         Scenario:
            1. Revert  environment
            2. Upload tarball
            3. Check that it uploaded
            4. Extract data
            5. Get available releases
            6. Run upgrade script
            7. Check that new release appears
            8. Put new release into cluster
            9. Run cluster update
            10. Get cluster net configuration
            11. Check is services are restarted
            12. Check is packages are updated
            13. Run OSTF
            14. Create snapshot

        """
        logger.info("snapshot name is {0}".format(self.snapshot))

        if not self.env.get_virtual_environment().has_snapshot(self.snapshot):
            logger.error('There is no shaphot found {0}'.format(self.snapshot))
            raise SkipTest('Can not find snapshot {0}'.format(self.snapshot))

        #  1. Revert  environment

        self.env.revert_snapshot(self.snapshot)

        logger.info("Start upload upgrade archive")
        node_ssh = self.env.get_ssh_to_remote(self.fuel_web.admin_node_ip)

        # 2. Upload tarball
        checkers.upload_tarball(
            node_ssh=node_ssh, tar_path=hlp_data.TARBALL_PATH,
            tar_target='/var/tmp')

        logger.info("Archive should upload. "
                    "Lets check that it exists on master node ...")
        #  3. Check that it uploaded
        checkers.check_tarball_exists(node_ssh, os.path.basename(
            hlp_data.TARBALL_PATH), '/var/tmp')

        logger.info("Extract archive to the /var/tmp")

        # 4. Extract data
        checkers.untar(node_ssh, os.path.basename(
            hlp_data.TARBALL_PATH), '/var/tmp')

        logger.info("Get release ids for deployed operation"
                    " system before upgrade..")

        # Get cluster nodes
        nailgun_nodes = [
            self.fuel_web.get_nailgun_node_by_devops_node(node)
            for node in self.env.nodes().slaves
            if self.fuel_web.get_nailgun_node_by_devops_node(node)]

        # Try to remember installed nova-packages before update
        p_version_before = {}
        for node in nailgun_nodes:
            remote = self.fuel_web.get_ssh_for_node(node["devops_name"])
            res = checkers.get_package_versions_from_node(
                remote=remote, name="nova", os_type=hlp_data.OPENSTACK_RELEASE)
            p_version_before[node["devops_name"]] = res

        # 5. Get available releases
        available_releases_before = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)

        logger.info('Time to run upgrade...')

        # 6. Run upgrade script

        checkers.run_script(node_ssh, '/var/tmp', 'upgrade.sh')
        logger.info('Check if the upgrade complete..')

        checkers.wait_upgrade_is_done(node_ssh=node_ssh,
                                      phrase='*** UPGRADE DONE SUCCESSFULLY',
                                      timeout=600 * 10)

        available_releases_after = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)

        logger.info('release ids list after upgrade is {0}'.format(
            available_releases_after))
        # 7. Check that new release appears
        assert_true(
            len(available_releases_after) > len(available_releases_before),
            "There is no new release, release ids before {0},"
            " release ids after {1}". format(
                available_releases_before, available_releases_after))

        if 'Ubuntu' in hlp_data.OPENSTACK_RELEASE:
            res = utils.get_yaml_to_json(
                node_ssh,
                '/etc/puppet/{0}/manifests/ubuntu-versions.yaml'.format(
                    hlp_data.RELEASE_VERSION))
            res_packages = json.loads(res[0])
            logger.debug('what we have in res_packages {0}'.format(
                res_packages))
        else:
            res = utils.get_yaml_to_json(
                node_ssh,
                '/etc/puppet/{0}/manifests/centos-versions.yaml'.format(
                    hlp_data.RELEASE_VERSION))
            res_packages = json.loads(res[0])
            logger.debug('what we have in res_packages {0}'.format(
                res_packages))

        cluster_id = self.fuel_web.get_last_created_cluster()
        logger.debug("Cluster id is {0}".format(cluster_id))

        release_version = hlp_data.RELEASE_VERSION
        logger.debug("Release version is {0}".format(release_version))

        # 8. Put new release into cluster
        if release_version:
            added_release = self.fuel_web.get_releases_list_for_os(
                release_name=hlp_data.OPENSTACK_RELEASE,
                release_version=release_version)
            logger.debug("Does we have here release id ? {0}".format(
                release_version))
        else:
            added_release = [id for id in available_releases_after
                             if id not in available_releases_before]

        # get nova pids on controller before update
        ssh_to_controller = self.fuel_web.get_ssh_for_node(
            [n["devops_name"] for n in nailgun_nodes
             if 'controller' in n['roles']][0])

        nova_controller_services = ['nova-api', 'nova-cert',
                                    'nova-objectstore', 'nova-conductor',
                                    'nova-scheduler']

        nova_pids_before = utils.nova_service_get_pid(
            ssh_to_controller, nova_controller_services)

        logger.debug('Nova pids on controller before {0}'.format(
            nova_pids_before))

        # 9. Run cluster update
        self.fuel_web.update_cluster(
            cluster_id=cluster_id,
            data={
                'pending_release_id': added_release[0],
                'release_id': self.fuel_web.get_cluster_release_id(
                    cluster_id)})

        logger.info('Huh all preparation for update are done.'
                    ' It is time to update cluster ...')

        self.fuel_web.run_update(cluster_id=cluster_id,
                                 timeout=hlp_data.UPDATE_TIMEOUT, interval=20)

        # 10. Get cluster net configuration

        cluster_net = self.fuel_web.client.get_cluster(
            cluster_id)['net_provider']

        logger.debug('cluster net is {0}'.format(cluster_net))

        # 11. Check is services are restarted
        if 'Ubuntu' in hlp_data.OPENSTACK_RELEASE:
            utils.check_if_service_restarted_ubuntu(
                ssh_to_controller, ["keystone'",
                                    "glance-registry'",
                                    "glance-api'",
                                    "heat-api-cfn'",
                                    "heat-engine'",
                                    "heat-api'",
                                    "heat-api-cloudwatch'",
                                    "nova-novncproxy'"])
        else:
            utils.check_if_service_restarted_centos(
                ssh_to_controller, ["keystone",
                                    "glance-registry",
                                    "glance-api",
                                    "heat-api-cfn",
                                    "heat-engine",
                                    "heat-api",
                                    "heat-api-cloudwatch",
                                    "nova-novncproxy"])

        # get nova pids on controller after update
        nova_pids_after = utils.nova_service_get_pid(
            ssh_to_controller, nova_controller_services)

        logger.debug('Nova pids on controller before {0}'.format(
            nova_pids_before))

        assert_not_equal(nova_pids_before, nova_pids_after)

        # 12. Check is packages are updated

        if 'Ubuntu' in hlp_data.OPENSTACK_RELEASE:
            for package in packages_fixture.dep:
                packages_fixture.dep[package] = res_packages[package]
                logger.debug("Current state of dict is {0}".format(
                    packages_fixture.dep))
            for key in packages_fixture.dep:
                res = checkers.get_package_versions_from_node(
                    ssh_to_controller, name=key, os_type='Ubuntu')
                logger.debug('res_from_node is {0}'.format(res))
                assert_true(
                    packages_fixture.dep[key] in res,
                    "Wrong version of package {0}. "
                    "Should be {1} but get {2}".format(
                        key, packages_fixture.dep[key], res))
        else:
            for package in packages_fixture.rpm:
                packages_fixture.rpm[package] = res_packages[package]
                logger.debug("Current state of dict is")
            for key in packages_fixture.rpm:
                res = checkers.get_package_versions_from_node(
                    ssh_to_controller, name=key,
                    os_type=hlp_data.OPENSTACK_RELEASE)
                assert_true(
                    packages_fixture.rpm[key] in res,
                    "Wrong version of package {0}. "
                    "Should be {1} but get {2}".format(
                        key, packages_fixture.rpm[key], res))
        p_version_after = {}
        for node in nailgun_nodes:
            remote = self.fuel_web.get_ssh_for_node(node["devops_name"])
            res = checkers.get_package_versions_from_node(
                remote=remote, name="openstack",
                os_type=hlp_data.OPENSTACK_RELEASE)
            p_version_after[node["devops_name"]] = res

        logger.info("packages after {0}".format(p_version_after))
        logger.info("packages before {0}".format(p_version_before))

        assert_true(p_version_before != p_version_after)

        # 13. Run OSTF
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        # 14. Create snapshot
        self.env.make_snapshot('{0}_and_patch'.format(self.snapshot))

    # TODO (tleontovich) enailbe if rollback will be available
    #@test(depends_on=[deploy_and_patch])
    @log_snapshot_on_error
    def deploy_and_rollback(self):
        """Rollback/Downgrade os on reverted env

         Scenario:
            1. Revert  patched environment
            2. Get release ids
            2. Identify release id for rollback/downgrade
            3. Run rollback/downgrade
            4. Check that operation was successful
            5. Run OSTF

        """

        logger.info("snapshot name is {0}".format(self.snapshot))

        if not self.env.get_virtual_environment().has_snapshot(
                '{0}_and_patch'.format(self.snapshot)):
            raise SkipTest('Can not find snapshot {0}'.format(self.snapshot))

        self.env.revert_snapshot('{0}_and_patch'.format(self.snapshot))

        logger.info("Get release ids for deployed operation"
                    " system before rollback..")

        # Get cluster nodes
        nailgun_nodes = [
            self.fuel_web.get_nailgun_node_by_devops_node(node)
            for node in self.env.nodes().slaves
            if self.fuel_web.get_nailgun_node_by_devops_node(node)]

        logger.info("Find next nodes {0}".format(nailgun_nodes))

        # Try to remember installed nova-packages before update
        p_version_before = {}
        for node in nailgun_nodes:
            remote = self.fuel_web.get_ssh_for_node(node["devops_name"])
            res = checkers.get_package_versions_from_node(
                remote=remote, name="nova", os_type=hlp_data.OPENSTACK_RELEASE)
            p_version_before[node["devops_name"]] = res

        avail_release_ids = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)

        logger.info('Available release ids before rollback {0}'.format(
            avail_release_ids))
        cluster_id = self.fuel_web.get_last_created_cluster()
        cluster_release_id = self.fuel_web.get_cluster_release_id(
            cluster_id)

        logger.info('Time to run rollback...')

        self.fuel_web.update_cluster(
            cluster_id=cluster_id,
            data={
                'pending_release_id': [i for i in avail_release_ids
                                       if i != cluster_release_id][0],
                'release_id': self.fuel_web.get_cluster_release_id(
                    cluster_id)})

        self.fuel_web.run_update(cluster_id=cluster_id,
                                 timeout=hlp_data.UPDATE_TIMEOUT, interval=20)

        # Check packages after

        p_version_after = {}
        for node in nailgun_nodes:
            remote = self.fuel_web.get_ssh_for_node(node["devops_name"])
            res = checkers.get_package_versions_from_node(
                remote=remote, name="nova", os_type=hlp_data.OPENSTACK_RELEASE)
            p_version_after[node["devops_name"]] = res

        logger.info("packages after {0}".format(p_version_after))
        logger.info("packages before {0}".format(p_version_before))

        # TODO tleontovich: Add assert for packages, when test repo will avail

        self.fuel_web.run_ostf(cluster_id=cluster_id,)

        self.env.make_snapshot('{0}_and_rollback'.format(self.snapshot))


@factory
def generate_patch_tests():
    snap = hlp_data.SNAPSHOT.split(",")
    return [TestPatch(s) for s in snap]
