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

from proboscis.asserts import assert_equal
from proboscis import test
from proboscis import SkipTest
from devops.helpers.helpers import _wait
from devops.helpers.helpers import wait

from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers.decorators import create_diagnostic_snapshot
from fuelweb_test.helpers import os_actions
from fuelweb_test import logger
from fuelweb_test import settings as hlp_data
from fuelweb_test.tests import base_test_case as base_test_data


@test(groups=["upgrade"])
class UpgradeFuelMaster(base_test_data.TestBasic):
    @classmethod
    def check_upgraded_kernel(cls, admin_remote, slave_remote):
        #the archive contains several versions of the kernel
        #regular expression will pick the newer one
        #that is actually gets installed
        cmd = r"find /var/upgrade/repos/*/ubuntu/ -type f -name" \
              r" 'linux-image-*.deb' -printf '%f\n' | sed -rn " \
              r"'s/^linux-image-([0-9, \.]+(\-[0-9]+)?)-.*/\1/p' |" \
              r" sort -rV | " \
              r"head -1"
        expected_kernel = ''.join(admin_remote.execute(
            cmd)['stdout']).rstrip()
        logger.debug("kernel version from repos is {0}".format(
            expected_kernel))
        kernel = UpgradeFuelMaster.get_slave_kernel(slave_remote)
        checkers.check_kernel(kernel, expected_kernel)

    @classmethod
    def get_slave_kernel(cls, slave_remote):
        kernel = ''.join(slave_remote.execute(
            r"uname -r | sed -rn"
            r" 's/^([0-9, \.]+(\-[0-9]+)?)-.*/\1/p'")['stdout']).rstrip()
        logger.debug("slave kernel is {0}".format(kernel))
        return kernel

    @test(groups=["upgrade_ha_one_controller"])
    @log_snapshot_on_error
    def upgrade_ha_one_controller_env(self):
        """Upgrade ha one controller deployed cluster with ceph

        Scenario:
            1. Revert snapshot with ha one controller ceph env
            2. Run upgrade on master
            3. Check that upgrade was successful
            4. Add another compute node
            5. Re-deploy cluster
            6. Run OSTF

        """

        if not self.env.get_virtual_environment().has_snapshot(
                'ceph_ha_one_controller_compact'):
            raise SkipTest()

        self.env.revert_snapshot("ceph_ha_one_controller_compact")
        cluster_id = self.fuel_web.get_last_created_cluster()
        remote = self.env.get_ssh_to_remote_by_name('slave-01')
        expected_kernel = self.get_slave_kernel(remote)

        checkers.upload_tarball(self.env.get_admin_remote(),
                                hlp_data.TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.get_admin_remote(),
                       os.path.basename(hlp_data.
                                        TARBALL_PATH), '/var')
        checkers.run_script(self.env.get_admin_remote(), '/var',
                            'upgrade.sh', password=
                            hlp_data.KEYSTONE_CREDS['password'])
        checkers.wait_upgrade_is_done(self.env.get_admin_remote(), 3000,
                                      phrase='*** UPGRADE DONE SUCCESSFULLY')
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_FROM,
                                           hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.wait_nodes_get_online_state(
            self.env.get_virtual_environment().nodes().slaves[:3])
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nailgun_upgrade_migration()
        self.env.bootstrap_nodes(
            self.env.get_virtual_environment().nodes().slaves[3:4])
        self.fuel_web.update_nodes(
            cluster_id, {'slave-04': ['compute']},
            True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            user='ceph1', tenant='ceph1', passwd='ceph1')
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=10, networks_count=1, timeout=300)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        if hlp_data.OPENSTACK_RELEASE_UBUNTU in hlp_data.OPENSTACK_RELEASE:
            remote = self.env.get_ssh_to_remote_by_name('slave-04')
            kernel = self.get_slave_kernel(remote)
            checkers.check_kernel(kernel, expected_kernel)
        create_diagnostic_snapshot(
            self.env, "pass", "upgrade_ha_one_controller_env")

        self.env.make_snapshot("upgrade_ha_one_controller")

    @test(groups=["upgrade_ha_one_controller_delete_node"])
    @log_snapshot_on_error
    def upgrade_ha_one_controller_delete_node(self):
        """Upgrade ha 1 controller deployed cluster with ceph and
           delete node from old cluster

        Scenario:
            1. Revert ceph_ha_one_controller_compact snapshot
            2. Run upgrade on master
            3. Check that upgrade was successful
            4. Delete one compute+ceph node
            5. Re-deploy cluster
            6. Run OSTF

        """

        if not self.env.get_virtual_environment().has_snapshot(
                'ceph_ha_one_controller_compact'):
            raise SkipTest()

        self.env.revert_snapshot("ceph_ha_one_controller_compact")
        cluster_id = self.fuel_web.get_last_created_cluster()
        checkers.upload_tarball(self.env.get_admin_remote(),
                                hlp_data.TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.get_admin_remote(),
                       os.path.basename(hlp_data.
                                        TARBALL_PATH), '/var')
        checkers.run_script(self.env.get_admin_remote(), '/var',
                            'upgrade.sh', password=
                            hlp_data.KEYSTONE_CREDS['password'])
        checkers.wait_upgrade_is_done(self.env.get_admin_remote(), 3000,
                                      phrase='*** UPGRADE DONE SUCCESSFULLY')
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_FROM,
                                           hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.wait_nodes_get_online_state(
            self.env.get_virtual_environment().nodes().slaves[:3])
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nailgun_upgrade_migration()
        nailgun_nodes = self.fuel_web.update_nodes(
            cluster_id, {'slave-03': ['compute', 'ceph-osd']}, False, True)
        task = self.fuel_web.deploy_cluster(cluster_id)
        self.fuel_web.assert_task_success(task)
        nodes = filter(lambda x: x["pending_deletion"] is True, nailgun_nodes)
        wait(
            lambda: self.fuel_web.is_node_discovered(nodes[0]),
            timeout=10 * 60
        )
        self.fuel_web.run_ostf(cluster_id=cluster_id, should_fail=1)
        self.env.make_snapshot("upgrade_ha_one_controller_delete_node")

    @test(groups=["upgrade_ha"])
    @log_snapshot_on_error
    def upgrade_ha_env(self):
        """Upgrade ha deployed cluster

        Scenario:
            1. Revert snapshot with neutron gre ha env
            2. Run upgrade on master
            3. Check that upgrade was successful
            4. Check cluster is operable
            5. Create new ha cluster with 1 controller Vlan cluster
            6. Deploy cluster
            7. Run OSTF

        """
        if not self.env.get_virtual_environment().has_snapshot(
                'deploy_neutron_gre_ha'):
            raise SkipTest()

        self.env.revert_snapshot("deploy_neutron_gre_ha")
        cluster_id = self.fuel_web.get_last_created_cluster()
        available_releases_before = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)
        checkers.upload_tarball(self.env.get_admin_remote(),
                                hlp_data.TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.get_admin_remote(),
                       os.path.basename(hlp_data.
                                        TARBALL_PATH), '/var')
        checkers.run_script(self.env.get_admin_remote(), '/var',
                            'upgrade.sh', password=
                            hlp_data.KEYSTONE_CREDS['password'])
        checkers.wait_upgrade_is_done(self.env.get_admin_remote(), 3000,
                                      phrase='*** UPGRADE DONE SUCCESSFULLY')
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_FROM,
                                           hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.wait_nodes_get_online_state(
            self.env.get_virtual_environment().nodes().slaves[:5])
        self.fuel_web.assert_nailgun_upgrade_migration()
        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        available_releases_after = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)
        added_release = [id for id in available_releases_after
                         if id not in available_releases_before]
        self.env.bootstrap_nodes(
            self.env.get_virtual_environment().nodes().slaves[5:7])
        data = {
            'tenant': 'novaSimpleVlan',
            'user': 'novaSimpleVlan',
            'password': 'novaSimpleVlan'
        }
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_data.DEPLOYMENT_MODE,
            settings=data,
            release_id=added_release[0]
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-06': ['controller'],
                'slave-07': ['compute']
            }
        )
        self.fuel_web.update_vlan_network_fixed(
            cluster_id, amount=8, network_size=32)

        self.fuel_web.deploy_cluster_wait(cluster_id)

        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            data['user'], data['password'], data['tenant'])
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=6, networks_count=8, timeout=300)
        if hlp_data.OPENSTACK_RELEASE_UBUNTU in hlp_data.OPENSTACK_RELEASE:
            remote = self.env.get_ssh_to_remote_by_name('slave-06')
            self.check_upgraded_kernel(self.env.get_admin_remote(), remote)
        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)
        self.env.make_snapshot("upgrade_ha")

    @test(groups=["deploy_ha_after_upgrade"])
    @log_snapshot_on_error
    def deploy_ha_after_upgrade(self):
        """Upgrade and deploy new ha cluster

        Scenario:
            1. Revert snapshot with ha 1 controller ceph env
            2. Run upgrade on master
            3. Check that upgrade was successful
            4. Re-deploy cluster
            5. Run OSTF

        """
        if not self.env.get_virtual_environment().has_snapshot(
                'ceph_ha_one_controller_compact'):
            raise SkipTest()

        self.env.revert_snapshot("ceph_ha_one_controller_compact")
        cluster_id = self.fuel_web.get_last_created_cluster()
        available_releases_before = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)
        checkers.upload_tarball(self.env.get_admin_remote(),
                                hlp_data.TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.get_admin_remote(),
                       os.path.basename(hlp_data.TARBALL_PATH),
                       '/var')
        checkers.run_script(self.env.get_admin_remote(), '/var',
                            'upgrade.sh', password=
                            hlp_data.KEYSTONE_CREDS['password'])
        checkers.wait_upgrade_is_done(self.env.get_admin_remote(), 3000,
                                      phrase='*** UPGRADE DONE SUCCESSFULLY')
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_FROM,
                                           hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.wait_nodes_get_online_state(
            self.env.get_virtual_environment().nodes().slaves[:3])
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_TO)
        self.fuel_web.assert_nailgun_upgrade_migration()
        available_releases_after = self.fuel_web.get_releases_list_for_os(
            release_name=hlp_data.OPENSTACK_RELEASE)
        added_release = [id for id in available_releases_after
                         if id not in available_releases_before]
        self.env.bootstrap_nodes(
            self.env.get_virtual_environment().nodes().slaves[3:9])
        segment_type = 'vlan'
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_data.DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type
            },
            release_id=added_release[0]
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-04': ['controller'],
                'slave-05': ['controller'],
                'slave-06': ['controller'],
                'slave-07': ['compute'],
                'slave-08': ['compute'],
                'slave-09': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        if hlp_data.OPENSTACK_RELEASE_UBUNTU in hlp_data.OPENSTACK_RELEASE:
            remote = self.env.get_ssh_to_remote_by_name('slave-04')
            self.check_upgraded_kernel(self.env.get_admin_remote(), remote)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id)
        self.env.make_snapshot("deploy_ha_after_upgrade")


@test(groups=["rollback"])
class RollbackFuelMaster(base_test_data.TestBasic):
    @test(groups=["rollback_automatic_ha"])
    @log_snapshot_on_error
    def rollback_automatically_ha_env(self):
        """Rollback manually ha deployed cluster

        Scenario:
            1. Revert snapshot with neutron gre ha env
            2. Add raise exception to openstack.py file
            3. Run upgrade on master
            4. Check that rollback starts automatically
            5. Check that cluster was not upgraded
            6. Add 1 cinder node and re-deploy cluster
            7. Run OSTF

        """
        if not self.env.get_virtual_environment().has_snapshot(
                'deploy_neutron_gre_ha'):
            raise SkipTest()

        self.env.revert_snapshot("deploy_neutron_gre_ha")
        cluster_id = self.fuel_web.get_last_created_cluster()
        checkers.upload_tarball(self.env.get_admin_remote(),
                                hlp_data.TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.get_admin_remote(),
                       os.path.basename(hlp_data.
                                        TARBALL_PATH), '/var')
        checkers.run_script(self.env.get_admin_remote(), '/var', 'upgrade.sh',
                            password=
                            hlp_data.KEYSTONE_CREDS['password'],
                            rollback=True, exit_code=255)
        checkers.wait_rollback_is_done(self.env.get_admin_remote(), 3000)
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_TO,
                                           hlp_data.UPGRADE_FUEL_FROM)
        logger.debug("all containers are ok")
        _wait(lambda: self.fuel_web.get_nailgun_node_by_devops_node(
            self.env.get_virtual_environment(
            ).nodes().slaves[0]), timeout=120)
        logger.debug("all services are up now")
        self.fuel_web.wait_nodes_get_online_state(
            self.env.get_virtual_environment().nodes().slaves[:5])
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_FROM)

        self.env.bootstrap_nodes(
            self.env.get_virtual_environment().nodes().slaves[5:6])
        self.fuel_web.update_nodes(
            cluster_id, {'slave-06': ['cinder']},
            True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.env.make_snapshot("rollback_automatic_ha")

    @test(groups=["rollback_automatic_ha_one_controller"])
    @log_snapshot_on_error
    def rollback_automatically_ha_one_controller_env(self):
        """Rollback automatically ha one controller deployed cluster

        Scenario:
            1. Revert snapshot with deploy neutron gre env
            2. Add raise exception to docker_engine.py file
            3. Run upgrade on master
            4. Check that rollback starts automatically
            5. Check that cluster was not upgraded and run OSTf
            6. Add 1 cinder node and re-deploy cluster
            7. Run OSTF

        """
        if not self.env.get_virtual_environment().has_snapshot(
                'deploy_neutron_gre'):
            raise SkipTest()

        self.env.revert_snapshot("deploy_neutron_gre")
        cluster_id = self.fuel_web.get_last_created_cluster()
        remote = self.env.get_ssh_to_remote_by_name('slave-01')
        expected_kernel = UpgradeFuelMaster.get_slave_kernel(remote)

        checkers.upload_tarball(self.env.get_admin_remote(),
                                hlp_data.TARBALL_PATH, '/var')
        checkers.check_tarball_exists(self.env.get_admin_remote(),
                                      os.path.basename(hlp_data.
                                                       TARBALL_PATH),
                                      '/var')
        checkers.untar(self.env.get_admin_remote(),
                       os.path.basename(hlp_data.
                                        TARBALL_PATH), '/var')
        #we expect 255 exit code here because upgrade failed
        # and exit status is 255
        checkers.run_script(self.env.get_admin_remote(), '/var', 'upgrade.sh',
                            password=
                            hlp_data.KEYSTONE_CREDS['password'],
                            rollback=True, exit_code=255)
        checkers.wait_rollback_is_done(self.env.get_admin_remote(), 3000)
        checkers.check_upgraded_containers(self.env.get_admin_remote(),
                                           hlp_data.UPGRADE_FUEL_TO,
                                           hlp_data.UPGRADE_FUEL_FROM)
        logger.debug("all containers are ok")
        _wait(lambda: self.fuel_web.get_nailgun_node_by_devops_node(
            self.env.get_virtual_environment(
            ).nodes().slaves[0]), timeout=120)
        logger.debug("all services are up now")
        self.fuel_web.wait_nodes_get_online_state(
            self.env.get_virtual_environment().nodes().slaves[:3])
        self.fuel_web.assert_nodes_in_ready_state(cluster_id)
        self.fuel_web.assert_fuel_version(hlp_data.UPGRADE_FUEL_FROM)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.bootstrap_nodes(
            self.env.get_virtual_environment().nodes().slaves[3:4])
        self.fuel_web.update_nodes(
            cluster_id, {'slave-04': ['cinder']},
            True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        if hlp_data.OPENSTACK_RELEASE_UBUNTU in hlp_data.OPENSTACK_RELEASE:
            remote = self.env.get_ssh_to_remote_by_name('slave-04')
            kernel = UpgradeFuelMaster.get_slave_kernel(remote)
            checkers.check_kernel(kernel, expected_kernel)
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.env.make_snapshot("rollback_automatic_ha_one_controller")
