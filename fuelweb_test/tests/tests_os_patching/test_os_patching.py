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

import os
from proboscis.asserts import assert_true
from proboscis import factory
from proboscis import SkipTest
from proboscis import test

from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings as hlp_data
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger


@test(groups=["os_patching"])
class TestPatch(TestBasic):
    def __init__(self, snapshot):
        super(TestPatch, self).__init__()
        self.snapshot = snapshot
        self.deploy_and_patch.__func__.func_name = "{0}_and_patch".format(
            self.snapshot)
        self.deploy_and_rollback.__func__.func_name = "{0}_rollback".format(
            self.snapshot)

    @test
    @log_snapshot_on_error
    def deploy_and_patch(self):
        """Update os on reverted cluster

         Scenario:
            1. Revert  environment
            2. Upload tarball
            3. Check that it uploaded
            4. Extract data
            5. Get available releases
            6. Run update script
            7. Check that new release appears
            8. Put new release into cluster
            9. Run cluster update
            10. Run OSTF
            11. Create snapshot

        """

        if not self.env.get_virtual_environment().has_snapshot(self.snapshot):
            raise SkipTest()

        self.env.revert_snapshot(self.snapshot)

        logger.info("Start upload upgrade archive")
        node_ssh = self.env.get_ssh_to_remote(self.fuel_web.admin_node_ip)
        checkers.upload_tarball(
            node_ssh=node_ssh, tar_path=hlp_data.UPDATE_TARBALL_PATH,
            tar_target='/var/tmp')

        logger.info("Archive should upload. "
                    "Lets check that it exists on master node ...")

        checkers.check_tarball_exists(node_ssh, os.path.basename(
            hlp_data.UPDATE_TARBALL_PATH), '/var/tmp')

        logger.info("Extract archive to the /var/tmp")

        checkers.untar(node_ssh, os.path.basename(
            hlp_data.UPDATE_TARBALL_PATH), '/var/tmp')

        logger.info("Get release ids for deployed operation"
                    " system before upgrade..")

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

        available_releases_before = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)

        logger.info('Available release ids before upgrade {0}'.format(
            available_releases_before))

        logger.info('Time to run upgrade...')

        checkers.run_script(node_ssh, '/var/tmp',
                            "UPGRADERS='openstack' ./upgrade.sh")
        logger.info('Check if the upgrade complete..')

        checkers.wait_upgrade_is_done(node_ssh=node_ssh,
                                      phrase='*** UPGRADE DONE SUCCESSFULLY',
                                      timeout=60 * 10)

        logger.info('Get release ids list after upgrade')
        available_releases_after = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)

        logger.info('release ids list after upgrade is {0}'.format(
            available_releases_after))

        assert_true(
            len(available_releases_after) > len(available_releases_before),
            "There is no new release, release ids before {0},"
            " release ids after {1}". format(
                available_releases_before, available_releases_after))

        logger.debug("what we have here {0}".format(self.__class__))

        cluster_id = self.fuel_web.get_last_created_cluster()
        logger.debug("Cluster id is {0}".format(cluster_id))

        added_release = [id for id in available_releases_after
                         if id not in available_releases_before]

        self.fuel_web.update_cluster(
            cluster_id=cluster_id,
            data={
                'pending_release_id': added_release[0],
                'release_id': self.fuel_web.get_cluster_release_id(
                    cluster_id)})

        logger.info('Huh all preparation for update are done.'
                    ' It is time to update cluster ...')

        self.fuel_web.run_update(
            cluster_id=cluster_id, timeout=15 * 60, interval=20)

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

        self.env.make_snapshot('{0}_and_patch'.format(self.snapshot),
                               is_make=True)

    @test(depends_on=[deploy_and_patch])
    @log_snapshot_on_error
    def deploy_and_rollback(self):
        """Rollback os on reverted cluster

         Scenario:
            1. Revert  patched environment
            2. Get release ids
            2. Identify release id for rollback
            3. Run rollback
            4. Check that rollback was successful
            5. Run OSTF
            6. Create snapshot

        """

        if not self.env.get_virtual_environment().has_snapshot(
                '{0}_and_patch'.format(self.snapshot)):
            raise SkipTest()

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

        self.fuel_web.run_update(
            cluster_id=cluster_id, timeout=15 * 60, interval=20)

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

        self.env.make_snapshot('{0}_and_rollback'.format(self.snapshot),
                               is_make=True)


@factory
def generate_patch_tests():
    snap = hlp_data.SNAPSHOT.split(",")
    return [TestPatch(s) for s in snap]
