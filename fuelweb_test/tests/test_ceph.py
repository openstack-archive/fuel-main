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

import proboscis
import time

from proboscis.asserts import assert_true, assert_false
from proboscis import SkipTest
from proboscis import test

from fuelweb_test.helpers import os_actions
from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import ostf_test_mapping as map_ostf
from fuelweb_test import settings
from fuelweb_test.settings import NEUTRON_ENABLE
from fuelweb_test import logger
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["thread_1", "ceph"])
class CephCompact(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["ceph_ha_one_controller_compact",
                  "ha_one_controller_nova_ceph"])
    @log_snapshot_on_error
    def ceph_ha_one_controller_compact(self):
        """Deploy ceph in HA mode with 1 controller

        Scenario:
            1. Create cluster
            2. Add 1 node with controller and ceph OSD roles
            3. Add 2 node with compute and ceph OSD roles
            4. Deploy the cluster
            5. Check ceph status

        Duration 35m
        Snapshot ceph_ha_one_controller_compact
        """
        self.env.revert_snapshot("ready_with_3_slaves")
        data = {
            'volumes_ceph': True,
            'images_ceph': True,
            'volumes_lvm': False,
            'tenant': 'ceph1',
            'user': 'ceph1',
            'password': 'ceph1'
        }
        if NEUTRON_ENABLE:
            data["net_provider"] = 'neutron'
            data["net_segment_type"] = 'vlan'

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings=data)
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'ceph-osd'],
                'slave-02': ['compute', 'ceph-osd'],
                'slave-03': ['compute', 'ceph-osd']
            }
        )
        # Cluster deploy
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.check_ceph_status(cluster_id)

        # Run ostf
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.env.make_snapshot("ceph_ha_one_controller_compact")


@test(groups=["thread_3", "ceph"])
class CephCompactWithCinder(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_release],
          groups=["ceph_ha_one_controller_with_cinder"])
    @log_snapshot_on_error
    def ceph_ha_one_controller_with_cinder(self):
        """Deploy ceph with cinder in ha mode with 1 controller

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 2 nodes with cinder and ceph OSD roles
            5. Deploy the cluster
            6. Check ceph status
            7. Check partitions on controller node

        Duration 40m
        Snapshot ceph_ha_one_controller_with_cinder
        """
        try:
            self.check_run('ceph_ha_one_controller_with_cinder')
        except SkipTest:
            return

        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(
            self.env.get_virtual_environment().nodes().slaves[:4])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings={
                'volumes_ceph': False,
                'images_ceph': True,
                'volumes_lvm': True,
                'tenant': 'ceph2',
                'user': 'ceph2',
                'password': 'ceph2'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['cinder', 'ceph-osd'],
                'slave-04': ['cinder', 'ceph-osd']
            }
        )
        # Cluster deploy
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.check_ceph_status(cluster_id)

        disks = self.fuel_web.client.get_node_disks(
            self.fuel_web.get_nailgun_node_by_name('slave-01')['id'])

        logger.info("Current disk partitions are: \n{d}".format(d=disks))

        logger.info("Check unallocated space")
        # We expect failure here only for release 5.0 due to bug
        # https://bugs.launchpad.net/fuel/+bug/1306625, so it is
        # necessary to assert_true in the next release.
        assert_false(
            checkers.check_unallocated_space(disks, contr_img_ceph=True),
            "Check unallocated space on controller")

        # Run ostf
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.env.make_snapshot("ceph_ha_one_controller_with_cinder",
                               is_make=True)


@test(groups=["thread_3", "ceph", "image_based"])
class CephHA(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_release],
          groups=["ceph_ha", "ha_nova_ceph", "ha_neutron_ceph", "bvt_2"])
    @log_snapshot_on_error
    def ceph_ha(self):
        """Deploy ceph with cinder in HA mode

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller and ceph OSD roles
            3. Add 1 node with ceph OSD roles
            4. Add 2 nodes with compute and ceph OSD roles
            5. Deploy the cluster
            6. Check ceph status

        Duration 90m
        Snapshot ceph_ha

        """
        try:
            self.check_run('ceph_ha')
        except SkipTest:
            return

        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(
            self.env.get_virtual_environment().nodes().slaves[:6])
        csettings = {}
        if settings.NEUTRON_ENABLE:
            csettings = {
                "net_provider": 'neutron',
                "net_segment_type": "vlan"
            }
        csettings.update(
            {
                'volumes_ceph': True,
                'images_ceph': True,
                'volumes_lvm': False,
                'tenant': 'cephHA',
                'user': 'cephHA',
                'password': 'cephHA'
            }
        )
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings=csettings
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'ceph-osd'],
                'slave-02': ['controller', 'ceph-osd'],
                'slave-03': ['controller', 'ceph-osd'],
                'slave-04': ['compute', 'ceph-osd'],
                'slave-05': ['compute', 'ceph-osd'],
                'slave-06': ['ceph-osd']
            }
        )
        # Depoy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.check_ceph_status(cluster_id)

        # Run ostf
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.env.make_snapshot("ceph_ha", is_make=True)


@test(groups=["thread_4", "ceph"])
class CephRadosGW(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["ceph_rados_gw"])
    @log_snapshot_on_error
    def ceph_rados_gw(self):
        """Deploy ceph ha with 1 controller with RadosGW for objects

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 3 nodes with ceph-osd role
            5. Deploy the cluster
            6. Check ceph status
            7. Run OSTF tests
            8. Check the radosqw daemon is started

        Duration 40m
        Snapshot ceph_rados_gw

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings={
                'volumes_lvm': False,
                'volumes_ceph': True,
                'images_ceph': True,
                'objects_ceph': True,
                'tenant': 'rados',
                'user': 'rados',
                'password': 'rados'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['ceph-osd'],
                'slave-04': ['ceph-osd'],
                'slave-05': ['ceph-osd']
            }
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.check_ceph_status(cluster_id)

        try:
            self.fuel_web.run_single_ostf_test(
                cluster_id, test_sets=['smoke'],
                test_name=map_ostf.OSTF_TEST_MAPPING.get(
                    'Create volume and attach it to instance'))
        except AssertionError:
            logger.debug("Test failed from first probe,"
                         " we sleep 60 second try one more time "
                         "and if it fails again - test will fails ")
            time.sleep(60)
            self.fuel_web.run_single_ostf_test(
                cluster_id, test_sets=['smoke'],
                test_name=map_ostf.OSTF_TEST_MAPPING.get(
                    'Create volume and attach it to instance'))

        # Run ostf
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['smoke', 'sanity', 'platform_tests'])

        # Check the radosqw daemon is started
        remote = self.fuel_web.get_ssh_for_node('slave-01')
        radosgw_started = lambda: len(remote.check_call(
            'ps aux | grep "/usr/bin/radosgw -n '
            'client.radosgw.gateway"')['stdout']) == 3
        assert_true(radosgw_started(), 'radosgw daemon started')

        self.env.make_snapshot("ceph_rados_gw")


@test(groups=["thread_1", "ceph_migration"])
class VmBackedWithCephMigrationBasic(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["ceph_migration"])
    @log_snapshot_on_error
    def migrate_vm_backed_with_ceph(self):
        """Check VM backed with ceph migration in ha mode with 1 controller

        Scenario:
            1. Create cluster
            2. Add 1 node with controller and ceph OSD roles
            3. Add 2 node with compute and ceph OSD roles
            4. Deploy the cluster
            5. Check ceph status
            6. Run OSTF
            7. Create a new VM, assign floating ip
            8. Migrate VM
            9. Check cluster and server state after migration
            10. Terminate VM

        Duration 35m
        Snapshot vm_backed_with_ceph_live_migration

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise proboscis.SkipTest()

        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings={
                'volumes_ceph': True,
                'images_ceph': True,
                'ephemeral_ceph': True,
                'volumes_lvm': False
            }
        )

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'ceph-osd'],
                'slave-02': ['compute', 'ceph-osd'],
                'slave-03': ['compute', 'ceph-osd']
            }
        )
        creds = ("cirros", "test")

        # Cluster deploy
        self.fuel_web.deploy_cluster_wait(cluster_id)

        def _check():
            # Run volume test several times with hope that it pass
            test_path = map_ostf.OSTF_TEST_MAPPING.get(
                'Create volume and attach it to instance')
            logger.debug('Start to run test {0}'.format(test_path))
            self.fuel_web.run_single_ostf_test(
                cluster_id, test_sets=['smoke'],
                test_name=test_path)
        try:
            _check()
        except AssertionError:
            logger.debug(AssertionError)
            logger.debug("Test failed from first probe,"
                         " we sleep 60 second try one more time "
                         "and if it fails again - test will fails ")
            time.sleep(60)
            _check()

        # Run ostf
        self.fuel_web.run_ostf(cluster_id)

        # Create new server
        os = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id))

        logger.info("Create new server")
        srv = os.create_server_for_migration(
            scenario='./fuelweb_test/helpers/instance_initial_scenario')
        logger.info("Srv is currently in status: %s" % srv.status)

        logger.info("Assigning floating ip to server")
        floating_ip = os.assign_floating_ip(srv)
        srv_host = os.get_srv_host_name(srv)
        logger.info("Server is on host %s" % srv_host)

        time.sleep(100)

        md5before = os.get_md5sum(
            "/home/test_file",
            self.env.get_ssh_to_remote_by_name("slave-01"),
            floating_ip.ip, creds)

        logger.info("Get available computes")
        avail_hosts = os.get_hosts_for_migr(srv_host)

        logger.info("Migrating server")
        new_srv = os.migrate_server(srv, avail_hosts[0], timeout=200)
        logger.info("Check cluster and server state after migration")

        md5after = os.get_md5sum(
            "/home/test_file",
            self.env.get_ssh_to_remote_by_name("slave-01"),
            floating_ip.ip, creds)

        assert_true(
            md5after in md5before,
            "Md5 checksums don`t match."
            "Before migration md5 was equal to: {bef}"
            "Now it eqals: {aft}".format(bef=md5before, aft=md5after))

        res = os.execute_through_host(
            self.env.get_ssh_to_remote_by_name("slave-01"),
            floating_ip.ip, "ping -q -c3 -w10 %s | grep 'received' |"
            " grep -v '0 packets received'", creds)
        logger.info("Ping 8.8.8.8 result on vm is: %s" % res)

        logger.info("Check Ceph health is ok after migration")
        self.fuel_web.check_ceph_status(cluster_id)

        logger.info("Server is now on host %s" %
                    os.get_srv_host_name(new_srv))

        logger.info("Terminate migrated server")
        os.delete_instance(new_srv)
        assert_true(os.verify_srv_deleted(new_srv),
                    "Verify server was deleted")

        # Create new server

        logger.info("Create new server")
        srv = os.create_server_for_migration(
            scenario='./fuelweb_test/helpers/instance_initial_scenario')
        logger.info("Srv is currently in status: %s" % srv.status)

        logger.info("Assigning floating ip to server")
        floating_ip = os.assign_floating_ip(srv)
        srv_host = os.get_srv_host_name(srv)
        logger.info("Server is on host %s" % srv_host)

        logger.info("Create volume")
        vol = os.create_volume()
        logger.info("Attach volume to server")
        os.attach_volume(vol, srv)

        time.sleep(100)
        logger.info("Create filesystem and mount volume")
        os.execute_through_host(
            self.env.get_ssh_to_remote_by_name('slave-01'),
            floating_ip.ip, 'sudo sh /home/mount_volume.sh', creds)

        os.execute_through_host(
            self.env.get_ssh_to_remote_by_name('slave-01'),
            floating_ip.ip, 'sudo touch /mnt/file-on-volume', creds)

        logger.info("Get available computes")
        avail_hosts = os.get_hosts_for_migr(srv_host)

        logger.info("Migrating server")
        new_srv = os.migrate_server(srv, avail_hosts[0], timeout=120)
        logger.info("Check cluster and server state after migration")

        logger.info("Mount volume after migration")
        out = os.execute_through_host(
            self.env.get_ssh_to_remote_by_name('slave-01'),
            floating_ip.ip, 'sudo mount /dev/vdb /mnt', creds)

        logger.info("out of mounting volume is: %s" % out)

        assert_true("file-on-volume" in os.execute_through_host(
                    self.env.get_ssh_to_remote_by_name('slave-01'),
                    floating_ip.ip, "sudo ls /mnt", creds),
                    "File is abscent in /mnt")

        logger.info("Check Ceph health is ok after migration")
        self.fuel_web.check_ceph_status(cluster_id)

        logger.info("Server is now on host %s" %
                    os.get_srv_host_name(new_srv))

        logger.info("Terminate migrated server")
        os.delete_instance(new_srv)
        assert_true(os.verify_srv_deleted(new_srv),
                    "Verify server was deleted")

        self.env.make_snapshot(
            "vm_backed_with_ceph_live_migration")


@test(groups=["thread_1", "ceph_partitions"])
class CheckCephPartitionsAfterReboot(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["ceph_partitions"])
    @log_snapshot_on_error
    def check_ceph_partitions_after_reboot(self):
        """Check that Ceph OSD partitions are remounted after reboot

        Scenario:
            1. Create cluster in Ha mode with 1 controller
            2. Add 1 node with controller role
            3. Add 1 node with compute and Ceph OSD roles
            4. Add 1 node with Ceph OSD role
            5. Deploy the cluster
            7. Check Ceph status
            8. Read current partitions
            9. Warm-reboot Ceph nodes
            10. Read partitions again
            11. Check Ceph health
            12. Cold-reboot Ceph nodes
            13. Read partitions again
            14. Check Ceph health

        Duration 40m
        Snapshot check_ceph_partitions_after_reboot

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise proboscis.SkipTest()

        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE,
            settings={
                'volumes_ceph': True,
                'images_ceph': True,
                'ephemeral_ceph': True,
                'volumes_lvm': False
            }
        )

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute', 'ceph-osd'],
                'slave-03': ['ceph-osd']
            }
        )
        # Deploy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)
        for node in ["slave-02", "slave-03"]:
            logger.info("Get partitions for {node}".format(node=node))
            before_reboot_partitions = [checkers.get_ceph_partitions(
                self.env.get_ssh_to_remote_by_name(node),
                "/dev/vd{p}".format(p=part)) for part in ["b", "c"]]

            logger.info("Warm-restart nodes")
            self.fuel_web.warm_restart_nodes(
                [self.fuel_web.environment.get_virtual_environment().
                    get_node(name=node)])

            logger.info("Get partitions for {node} once again".format(
                node=node
            ))
            after_reboot_partitions = [checkers.get_ceph_partitions(
                self.env.get_ssh_to_remote_by_name(node),
                "/dev/vd{p}".format(p=part)) for part in ["b", "c"]]

            if before_reboot_partitions != after_reboot_partitions:
                logger.info("Partitions don`t match")
                logger.info("Before reboot: %s" % before_reboot_partitions)
                logger.info("After reboot: %s" % after_reboot_partitions)
                raise Exception()

            logger.info("Check Ceph health is ok after reboot")
            self.fuel_web.check_ceph_status(cluster_id)

            logger.info("Cold-restart nodes")
            self.fuel_web.cold_restart_nodes(
                [self.fuel_web.environment.get_virtual_environment().
                    get_node(name=node)])

            after_reboot_partitions = [checkers.get_ceph_partitions(
                self.env.get_ssh_to_remote_by_name(node),
                "/dev/vd{p}".format(p=part)) for part in ["b", "c"]]

            if before_reboot_partitions != after_reboot_partitions:
                logger.info("Partitions don`t match")
                logger.info("Before reboot: %s" % before_reboot_partitions)
                logger.info("After reboot: %s" % after_reboot_partitions)
                raise Exception()

            logger.info("Check Ceph health is ok after reboot")
            self.fuel_web.check_ceph_status(cluster_id)
