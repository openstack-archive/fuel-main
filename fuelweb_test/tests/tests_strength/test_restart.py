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

from fuelweb_test.helpers.checkers import check_ceph_health
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings
from fuelweb_test.settings import DEPLOYMENT_MODE_SIMPLE
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic

from proboscis import SkipTest
from proboscis import test


@test(groups=["thread_5", "ceph"])
class CephRestart(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_release],
          groups=["ceph_multinode_restart"])
    @log_snapshot_on_error
    def ceph_multinode_restart(self):
        """Deploy ceph with cinder in simple mode

        Scenario:
            1. Create cluster
            2. Add 1 node with controller and ceph OSD roles
            3. Add 1 node with compute role
            4. Add 2 nodes with cinder and ceph OSD roles
            5. Deploy the cluster
            7. Warm restart
            8. Check ceph status

        Snapshot None

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

        # Warm restart
        self.fuel_web.warm_restart_nodes(self.env.nodes().slaves[:4])

        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))
        self.fuel_web.run_ostf(cluster_id=cluster_id)


@test(groups=["thread_5", "ceph"])
class CephHARestart(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_release],
          groups=["ceph_ha_restart"])
    @log_snapshot_on_error
    def ceph_ha_restart(self):
        """Deploy ceph with cinder in HA mode

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller and ceph OSD roles
            3. Add 1 node with cinder and ceph OSD roles
            4. Add 2 nodes with compute and ceph OSD roles
            5. Deploy the cluster
            6. Check ceph status
            7. Cold retsart
            8. Check ceph status

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
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        # Destroy osd-node
        self.env.nodes().slaves[5].destroy()
        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))
        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=0)

        # Destroy compute node
        self.env.nodes().slaves[4].destroy()
        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        # Cold restart
        self.fuel_web.cold_restart_nodes(self.env.nodes().slaves[:4])

        check_ceph_health(self.env.get_ssh_to_remote_by_name('slave-01'))
        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.env.make_snapshot("ceph_ha")


@test(groups=["thread_5"])
class SimpleFlatRestart(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["simple_flat_warm_restart"])
    @log_snapshot_on_error
    def simple_flat_warm_restart(self):
        """Cold restart for simple environment

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy the cluster
            5. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs
            6. Turn off all nodes
            7. Start all nodes
            8. Run OSTF
            9. Warm restart
            10. Run OSTF

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        # Warm restart
        self.fuel_web.warm_restart_nodes(self.env.nodes().slaves[:2])

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])
