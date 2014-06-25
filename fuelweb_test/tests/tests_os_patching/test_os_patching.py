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
from proboscis import test

from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings as hlp_data
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test.tests import test_simple
from fuelweb_test import logger


@test(groups=["os_patching"])
class SimpleOsPatch(TestBasic):
    @test(depends_on=[test_simple.SimpleFlat.deploy_simple_flat],
          groups=["deploy_simple_flat_and_patch"])
    @log_snapshot_on_error
    def deploy_simple_flat_and_patch(self):
        """Update os on simple flat cluster

         Scenario:
            1. Revert "simple flat" environment
            2. Upload tarball
            3. Check that it uploaded
            4. Extract data
            5. Get available releases
            6. Run update script
            7. Check that new release appears
            8. Put release new release into cluster
            9. Run cluster update
            10. Run OSTF

        """
        self.env.revert_snapshot("deploy_simple_flat")

        logger.info("Start upload upgrade archive")
        node_ssh = self.env.get_ssh_to_remote(self.fuel_web.admin_node_ip)
        checkers.upload_tarball(
            node_ssh=node_ssh, tar_path=os.path.join(
                hlp_data.TARBALL_LOCAL_PATH,
                hlp_data.TARBALL_NAME), tar_target='/var/tmp')

        logger.info("Archive should upload. "
                    "Lets check that it exists on master node ...")

        checkers.check_tarball_exists(
            node_ssh,
            hlp_data.TARBALL_NAME, '/var/tmp')

        logger.info("Extract archive to the /var/tmp")

        checkers.untar(
            node_ssh,
            hlp_data.TARBALL_NAME, '/var/tmp')

        logger.info("Get release ids for deployed operation"
                    " system before upgrade..")

        available_releases_before = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)

        logger.info('Available release ids before upgrade {0}'.format(
            available_releases_before))

        logger.info('Time to run upgrade...')
        checkers.run_script(
            node_ssh,
            script_path='/var/tmp/update/', script_name='upgrade.sh')

        logger.info('Check if the upgrade complete..')

        checkers.wait_upgrade_is_done(node_ssh=node_ssh, timeout=60*10)

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
            cluster_id=cluster_id, timeout=15*60, interval=20)

        # Check release

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=2,
            failed_test_name=['Create volume and boot instance from it',
                              'Create volume and attach it to instance']
        )

        self.env.make_snapshot("simple_patch", is_make=True)
