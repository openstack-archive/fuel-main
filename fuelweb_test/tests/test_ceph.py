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
from fuelweb_test.settings import OPENSTACK_RELEASE, OPENSTACK_RELEASE_REDHAT, DEPLOYMENT_MODE_SIMPLE, DEPLOYMENT_MODE_HA
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
            3. Add 1 node with compute and ceph OSD roles
            4. Deploy the cluster
            5. Check ceph status

        Snapshot: ceph_multinode_compact

        """
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
            settings={
                'volumes_ceph': True,
                'images_ceph': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'ceph-osd'],
                'slave-02': ['compute', 'ceph-osd']
            }
        )
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
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_multinode_compact")

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=18
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
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.nodes().slaves[:4])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE,
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
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_multinode_with_cinder")

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
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.nodes().slaves[:6])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
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
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
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
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_ha")
        self.env.nodes().slaves[-1].destroy()

        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=18
        )

    @test(depends_on=[ceph_ha], groups=["ceph_ha_destroy_controller"])
    @log_snapshot_on_error
    def ceph_ha_destroy_controller(self):
        """Destroy OSD node for ceph HA

        Scenario:
            1. Revert snapshot: ceph_ha
            2. Destroy first controller + ceph OSD node
            3. Check ceph status
            4. Run OSTF

        """
        if OPENSTACK_RELEASE == OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ceph_ha")
        self.env.nodes().slaves[1].destroy()

        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))

        self.fuel_web.run_ostf(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            should_fail=4, should_pass=18
        )
