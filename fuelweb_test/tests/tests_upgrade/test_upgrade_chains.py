#    Copyright 2015 Mirantis, Inc.
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

from proboscis import test
from proboscis import SkipTest

from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.tests.base_test_case import SetupEnvironment

from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.decorators import log_snapshot_after_test
from fuelweb_test import logger
from fuelweb_test import settings as hlp_data
from fuelweb_test.tests import base_test_case as base_test_data


@test(groups=["upgrade_chains"])
class UpgradeFuelChains(base_test_data.TestBasic):
    """UpgradeChains."""  # TODO documentation

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["prepare_upgrade_env", "prepare_upgrade_env_classic"])
    @log_snapshot_after_test
    def prepare_upgrade_env(self):
        """Deploy cluster in ha mode with 1 controller and Neutron VLAN

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 2 nodes with compute role
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF

        Duration 35m
        Snapshot deploy_neutron_vlan

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": "vlan",
                'tenant': 'prepare_upgrade_env',
                'user': 'prepare_upgrade_env',
                'password': 'prepare_upgrade_env'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute', 'cinder'],
                'slave-03': ['compute', 'cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("prepare_upgrade_env", is_make=True)

    @test(groups=["upgrade_first_stage", "upgrade_first_stage_classic"])
    @log_snapshot_after_test
    def upgrade_first_stage(self):
        """Upgrade ha one controller deployed cluster and deploy new one

        Scenario:
            1. Revert snapshot with neutron ha one controller
            2. Run upgrade on master
            3. Check that upgrade was successful
            4. Run network verification
            5. Run OSTF
            6. Deploy new ceph ha one controller neutron vlan custer
            7. Run network verification
            8. Run OSTF

        """
        if not self.env.d_env.has_snapshot('prepare_upgrade_env'):
            raise SkipTest()
        self.env.revert_snapshot('prepare_upgrade_env')

        cluster_id = self.fuel_web.get_last_created_cluster()
        available_releases_before = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)
        checkers.upload_tarball(self.env.d_env.get_admin_remote(),
                                hlp_data.TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.d_env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.d_env.get_admin_remote(),
                       os.path.basename(hlp_data.
                                        TARBALL_PATH), '/var')
        checkers.run_script(self.env.d_env.get_admin_remote(),
                            '/var', 'upgrade.sh',
                            password=hlp_data.KEYSTONE_CREDS['password'])
        checkers.wait_upgrade_is_done(self.env.d_env.get_admin_remote(), 3000,
                                      phrase='*** UPGRADING MASTER NODE'
                                             ' DONE SUCCESSFULLY')
        checkers.check_upgraded_containers(self.env.d_env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_FROM,
                                           hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.wait_nodes_get_online_state(
            self.env.d_env.nodes().slaves[:3])
        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        available_releases_after = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)
        added_release = [id for id in available_releases_after
                         if id not in available_releases_before]
        self.env.bootstrap_nodes(
            self.env.d_env.nodes().slaves[3:6])
        data = {
            'tenant': 'upgrade_first_stage',
            'user': 'upgrade_first_stage',
            'password': 'upgrade_first_stage',
            'net_provider': 'neutron',
            'net_segment_type': 'vlan',
            'volumes_ceph': True,
            'images_ceph': True,
            'volumes_lvm': False
        }
        cluster_id = self.fuel_web.create_cluster(
            name='first_stage_upgrade',
            mode=hlp_data.DEPLOYMENT_MODE,
            settings=data,
            release_id=added_release[0]
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-04': ['controller'],
                'slave-05': ['compute', 'ceph-osd'],
                'slave-06': ['compute', 'ceph-osd']
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)
        self.env.make_snapshot("upgrade_first_stage", is_make=True)

    @test(groups=["upgrade_second_stage", "upgrade_second_stage_classic"])
    @log_snapshot_after_test
    def upgrade_second_stage(self):
        """Upgrade master second time with 2 available clusters

        Scenario:
            1. Revert snapshot upgrade_first_stage
            2. Run upgrade on master
            3. Check that upgrade was successful
            4. Run network verification on both clusters
            5. Run OSTF on both clusters
            6. Add 1 compute node to both clusters and
               re-deploy them one by one
            7. Run network verification on both clusters
            8. Run OSTF on both clusters

        """
        if not self.env.d_env.has_snapshot('upgrade_first_stage'):
            raise SkipTest()
        self.env.revert_snapshot('upgrade_first_stage')

        remote = self.env.d_env.get_admin_remote()
        remote.execute("rm -rf /var/*upgrade*")

        checkers.upload_tarball(remote,
                                hlp_data.TARBALL_PATH, '/var')
        checkers.check_tarball_exists(remote,
                                      os.path.basename(hlp_data.
                                                       TARBALL_PATH),
                                      '/var')
        checkers.untar(remote,
                       os.path.basename(hlp_data.
                                        TARBALL_PATH), '/var')
        checkers.run_script(remote,
                            '/var', 'upgrade.sh',
                            password=hlp_data.KEYSTONE_CREDS['password'])
        checkers.wait_upgrade_is_done(remote, 3000,
                                      phrase='*** UPGRADING MASTER NODE'
                                             ' DONE SUCCESSFULLY')
        checkers.check_upgraded_containers(remote,
                                           hlp_data.UPGRADE_FUEL_FROM,
                                           hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.wait_nodes_get_online_state(
            self.env.d_env.nodes().slaves[:6])
        self.env.bootstrap_nodes(
            self.env.d_env.nodes().slaves[6:8])

        cluster_ids = [cluster['id']
                       for cluster in self.fuel_web.client.list_clusters()]
        for cluster_id in cluster_ids:
            self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        first_cluster_id = sorted(cluster_ids)[0]
        second_cluster_id = sorted(cluster_ids)[1]
        logger.debug("first cluster id {0}, second cluster id"
                     " {1}".format(first_cluster_id, second_cluster_id))

        self.fuel_web.update_nodes(
            first_cluster_id, {'slave-07': ['compute']},
            True, False
        )
        self.fuel_web.deploy_cluster_wait(first_cluster_id)
        self.fuel_web.verify_network(first_cluster_id)
        self.fuel_web.run_ostf(cluster_id=first_cluster_id)

        self.fuel_web.update_nodes(
            second_cluster_id, {'slave-08': ['compute', 'ceph-osd']},
            True, False
        )
        self.fuel_web.deploy_cluster_wait(second_cluster_id)
        self.fuel_web.verify_network(second_cluster_id)
        self.fuel_web.run_ostf(cluster_id=second_cluster_id)
