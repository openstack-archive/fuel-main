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
import proboscis
import time

from fuelweb_test.helpers import os_actions
from fuelweb_test.helpers.checkers import check_ceph_health
from fuelweb_test.helpers.decorators import log_snapshot_on_error, debug
from fuelweb_test import settings
from fuelweb_test.tests import base_test_case

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@proboscis.test(groups=["thread_1", "ceph"])
class CephCompact(base_test_case.TestBasic):

    @proboscis.test(depends_on=
                    [base_test_case.SetupEnvironment.prepare_slaves_3],
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
            raise proboscis.SkipTest()

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


@proboscis.test(groups=["thread_1", "ceph"])
class CephCompactWithCinder(base_test_case.TestBasic):

    @proboscis.test(depends_on=
                    [base_test_case.SetupEnvironment.prepare_release],
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
            raise proboscis.SkipTest()

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

        self.env.make_snapshot("ceph_multinode_with_cinder")


@proboscis.test(groups=["thread_1", "ceph"])
class CephHA(base_test_case.TestBasic):

    @proboscis.test(depends_on=
                    [base_test_case.SetupEnvironment.prepare_release],
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
            raise proboscis.SkipTest()

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

        self.env.make_snapshot("ceph_ha")


@proboscis.test(groups=["thread_1", "ceph"])
class CephRadosGW(base_test_case.TestBasic):

    @proboscis.test(
        depends_on=[base_test_case.SetupEnvironment.prepare_slaves_5],
        groups=["ceph_rados_gw"])
    @log_snapshot_on_error
    def ceph_rados_gw(self):
        """Deploy ceph with RadosGW for objects

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Add 3 nodes with ceph-osd role
            5. Deploy the cluster
            6. Check ceph status
            7. Run OSTF tests
            8. Check the radosqw daemon is started

        Snapshot ceph_rados_gw

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise base_test_case.SkipTest()

        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_SIMPLE,
            settings={
                'volumes_lvm': False,
                'volumes_ceph': True,
                'images_ceph': True,
                'objects_ceph': True
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

        remote = self.fuel_web.get_ssh_for_node('slave-01')
        check_ceph_health(remote)

        # Run ostf
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['smoke', 'sanity', 'platform_tests'],
            should_fail=1)

        # Check the radosqw daemon is started
        radosgw_started = lambda: len(remote.check_call(
            'ps aux | grep "/usr/bin/radosgw -n '
            'client.radosgw.gateway"')['stdout']) == 3
        assert_true(radosgw_started(), 'radosgw daemon started')

        self.env.make_snapshot("ceph_rados_gw")
        self.env.make_snapshot("ceph_ha")


@proboscis.test(groups=["thread_1", "ceph"])
class VmBackedWithCephMigration(base_test_case.TestBasic):

    @proboscis.test(depends_on=
                    [base_test_case.SetupEnvironment.prepare_slaves_3],
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
            raise proboscis.SkipTest()

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

        # Cluster deploy
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Create new server
        os = os_actions.OpenStackActions(
            self.fuel_web.get_nailgun_node_by_name("slave-01")["ip"])

        logger.info("Create new server")
        srv = os.create_server()
        logger.info("Srv is currently in status: %s" % srv.status)

        if srv.status != "ERROR":
            logger.info("Assigning floating ip to server")
            floating_ip = os.assign_floating_ip(srv)
            srv_host = os.get_srv_host_name(srv)
            logger.info("Server is on host %s" % srv_host)

            time.sleep(100)
            logger.info("Execute command on srv - create file")

            md5sum = os.create_file_on_vm(
                "test_file", self.env.get_ssh_to_remote_by_name("slave-01"),
                floating_ip.ip)

            logger.info("Get available computes")
            avail_hosts = os.get_hosts_for_migr(srv_host)

            logger.info("Migrating server")
            new_srv = os.migrate_server(srv, avail_hosts[0])
            logger.info("Check cluster and server state after migration")

            if new_srv.status != "ACTIVE":
                raise Exception()

            os.check_file_exists(
                "test_file", md5sum,
                self.env.get_ssh_to_remote_by_name("slave-01"),
                floating_ip.ip)

            logger.info("Check Ceph health is ok after migration")
            check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

            logger.info("Server is now on host %s" %
                        os.get_srv_host_name(new_srv))

            logger.info("Terminate migrated server")
            os.delete_srv(new_srv)
        else:
            logger.info("Instance is in ERROR status")
            raise Exception()

        self.env.make_snapshot("vm_backed_with_ceph_live_migration")
