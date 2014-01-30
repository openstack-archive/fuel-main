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

from proboscis import test, SkipTest

from fuelweb_test.helpers import os_actions
from fuelweb_test.helpers.checkers import check_ceph_health
from fuelweb_test.helpers.decorators import log_snapshot_on_error, debug
from fuelweb_test import settings
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test(groups=["thread_1", "ceph"])
class CephCompact(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["ceph_multinode_compact"])
    @log_snapshot_on_error
    def ceph_multinode_compact(self):
        """Deploy ceph in simple mode

        Scenario:
            1. Create cluster
            2. Add 1 node with controller and ceph OSD roles
            3. Add 2 node with compute and ceph OSD roles
            4. Deploy the cluster
            5. Check ceph status

        Snapshot ceph_multinode_compact

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'volumes_ceph': True,
                'images_ceph': True
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
        # Cluster deploy
        self.fuel_web.deploy_cluster_wait(cluster_id)
        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        # Run ostf
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=4)

        self.env.make_snapshot("ceph_multinode_compact")


@test(groups=["thread_1", "ceph"])
class CephCompactWithCinder(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_release],
          groups=["ceph_multinode_with_cinder"])
    @log_snapshot_on_error
    def ceph_multinode_with_cinder(self):
        """Deploy ceph with cinder in simple mode

        Scenario:
            1. Create cluster
            2. Add 1 node with controller and ceph OSD roles
            3. Add 1 node with compute role
            4. Add 2 nodes with cinder and ceph OSD roles
            5. Deploy the cluster
            6. Check ceph status

        Snapshot ceph_multinode_with_cinder

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.nodes().slaves[:4])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'volumes_ceph': True,
                'images_ceph': True
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
        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        # Run ostf
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=4)

        # Cold restart
        self.fuel_web.restart_nodes(self.env.nodes().slaves[:4])

        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=4)

        self.env.make_snapshot("ceph_multinode_with_cinder")


@test(groups=["thread_1", "ceph"])
class CephHA(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_release],
          groups=["ceph_ha"])
    @log_snapshot_on_error
    def ceph_ha(self):
        """Deploy ceph with cinder in HA mode

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller and ceph OSD roles
            3. Add 1 node with cinder and ceph OSD roles
            4. Add 2 nodes with compute and ceph OSD roles
            5. Deploy the cluster
            6. Check ceph status

        Snapshot ceph_ha

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.nodes().slaves[:6])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings={
                'volumes_ceph': True,
                'images_ceph': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'ceph-osd'],
                'slave-02': ['controller', 'ceph-osd'],
                'slave-03': ['controller', 'ceph-osd'],
                'slave-04': ['compute', 'ceph-osd'],
                'slave-05': ['compute', 'ceph-osd'],
                'slave-06': ['cinder', 'ceph-osd']
            }
        )
        # Depoy cluster
        self.fuel_web.deploy_cluster_wait(cluster_id)
        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        # Run ostf
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=4)

        # Destroy osd-node
        self.env.nodes().slaves[3].destroy()
        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'),
                          recovery_timeout=True)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=4)

        # Destroy compute node
        self.env.nodes().slaves[4].destroy()
        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'),
                          recovery_timeout=True)
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=4)

        # Cold restart
        self.fuel_web.restart_nodes(self.env.nodes().slaves[:4])

        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=4)

        self.env.make_snapshot("ceph_ha")


@test(groups=["thread_1", "ceph"])
class VmBackedWithCephMigration(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["ceph"])
    @log_snapshot_on_error
    def migrate_vm_backed_with_ceph(self):
        """Check VM backed with ceph migration in simple mode

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

        Snapshot vm_backed_with_ceph_live_migration

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
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

        ssh_to_controller = self.env.get_ssh_to_remote_by_name('slave-01')
        # Cluster deploy
        self.fuel_web.deploy_cluster_wait(cluster_id)
        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        # Run ostf
        self.fuel_web.run_ostf(
             cluster_id=cluster_id,
            should_fail=4)

        # Create new server
        os = os_actions.OpenStackActions(
            self.fuel_web.get_nailgun_node_by_name("slave-01")["ip"])

        logger.info("Create new server")
        srv = os.create_server()

        logger.info("Assigning floating ip to server")
        floating_ip = os.assign_floating_ip(srv)
        srv_host = os.get_srv_host_name(srv)
        logger.info("Server is now on host %s" % srv_host)

        logger.info("Get available computes")
        avail_hosts = os.get_hosts_for_migr(srv_host)

        logger.info("Migrating server")
        new_srv = os.migrate_server(srv, avail_hosts[0])
        logger.info("Check cluster and server state after migration")

        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        # TODO: add more params to check
        # Paramters that shouldn`t have changed:
        unchanged = {"status": "ACTIVE"}

        res = os.check_srv_state_after_migration(new_srv,
                                                 unchanged, changed)
        logger.info("The results of changed and unchanged: %s" % res)
        logger.info("Server is now on host %s" % \
                    os.get_srv_host_name(new_srv))

        logger.info("Terminate migrated server")
        os.delete_srv(new_srv)

        self.env.make_snapshot("vm_backed_with_ceph_live_migration")
