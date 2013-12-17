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

        Snapshot: ceph_multinode_compact

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
        # Just to change default configuration of disk
        disk_size = settings.NODE_VOLUME_SIZE * 1000 - 600
        image_size = 10000
        ceph_size = disk_size - image_size

        for node_name in ['slave-01', 'slave-02', 'slave-03']:
            node = self.fuel_web.get_nailgun_node_by_name(node_name)
            self.fuel_web.update_node_disk(
                node['id'],
                {
                    'vda': {'os': disk_size, 'image': 0},
                    'vdb': {'image': image_size, 'ceph': ceph_size}
                })

        self.fuel_web.deploy_cluster_wait(cluster_id)
        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        self.env.make_snapshot("ceph_multinode_compact")

    @test(depends_on=[ceph_multinode_compact],
          groups=["ceph_multinode_compact_ostf"])
    @log_snapshot_on_error
    def ceph_multinode_compact_ostf(self):
        """Run OSTF on deployed cluster with ceph in simple mode

        Scenario:
            1. Revert snapshot: ceph_multinode_compact
            2. Run OSTF

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_multinode_compact")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=19
        )


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

        Snapshot: ceph_multinode_with_cinder

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
        self.fuel_web.deploy_cluster_wait(cluster_id)
        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        self.env.make_snapshot("ceph_multinode_with_cinder")

    @test(depends_on=[ceph_multinode_with_cinder],
          groups=["ceph_multinode_with_cinder_ostf"])
    @log_snapshot_on_error
    def ceph_multinode_with_cinder_ostf(self):
        """Run OSTF on deployed cluster with ceph and cider in simple mode

        Scenario:
            1. Revert snapshot: ceph_multinode_compact
            2. Run OSTF

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_multinode_with_cinder")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=18
        )

    @test(depends_on=[ceph_multinode_with_cinder_ostf],
          groups=["ceph_multinode_with_cinder_cold_restart"])
    @log_snapshot_on_error
    def ceph_multinode_with_cinder_cold_restart(self):
        """Cold restart for Simple environment

        Scenario:
            1. Revert snapshot: ceph_multinode_with_cinder
            2. Turn off all nodes
            3. Start all nodes
            4. Check ceph status

            5. Run OSTF

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_multinode_with_cinder")
        self.fuel_web.restart_nodes(self.env.nodes().slaves[:4])

        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))
        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=18
        )


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

        Snapshot: ceph_ha

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
        self.fuel_web.deploy_cluster_wait(cluster_id)
        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        self.env.make_snapshot("ceph_ha")

    @test(depends_on=[ceph_ha], groups=["ceph_ha_ostf"])
    @log_snapshot_on_error
    def ceph_ha_ostf(self):
        """Run OSTF on deployed cluster with ceph and cider in HA mode

        Scenario:
            1. Revert snapshot: ceph_ha
            2. Run OSTF

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_ha")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=18
        )

    @test(depends_on=[ceph_ha], groups=["ceph_ha_destroy_osd"])
    @log_snapshot_on_error
    def ceph_ha_destroy_osd(self):
        """Destroy OSD node for ceph HA

        Scenario:
            1. Revert snapshot: ceph_ha
            2. Destroy cinder + ceph osd node
            3. Check ceph status
            4. Run OSTF

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_ha")
        self.env.nodes().slaves[-1].destroy()

        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=18
        )

    @test(depends_on=[ceph_ha], groups=["ceph_ha_destroy_compute"])
    @log_snapshot_on_error
    def ceph_ha_destroy_compute(self):
        """Destroy OSD node for ceph HA

        Scenario:
            1. Revert snapshot: ceph_ha
            2. Destroy first compute + ceph OSD node
            3. Check ceph status
            4. Run OSTF

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_ha")
        self.env.nodes().slaves[4].destroy()

        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=18
        )

    @test(depends_on=[ceph_ha_ostf], groups=["ceph_ha_cold_restart"])
    @log_snapshot_on_error
    def ceph_ha_cold_restart(self):
        """Cold restart for HA environment

        Scenario:
            1. Revert snapshot: ceph_ha
            2. Turn off all nodes
            3. Start all nodes
            4. Check ceph status
            5. Run OSTF

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_ha")
        self.fuel_web.restart_nodes(self.env.nodes().slaves[:6])

        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))
        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=18
        )
