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

from proboscis import SkipTest
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings
from fuelweb_test.tests import base_test_case


@test(groups=["huge_environments"])
class HugeEnvironments(base_test_case.TestBasic):
    @test(depends_on=[base_test_case.SetupEnvironment.prepare_release],
          groups=["nine_nodes_mixed"])
    @log_snapshot_on_error
    def nine_nodes_mixed(self):
        """Deploy cluster with mixed roles on 9 nodes in HA mode

        Scenario:
            1. Create cluster
            2. Add 4 nodes as controllers with ceph OSD roles
            3. Add 5 nodes as compute with ceph OSD roles
            4. Turn on Savanna and Ceilometer
            5. Deploy the cluster
            6. Check networks and OSTF

        Snapshot None

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.nodes().slaves[:9])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings={
                'volumes_ceph': True,
                'images_ceph': True,
                'sahara': True,
                'ceilometer': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'ceph-osd'],
                'slave-02': ['controller', 'ceph-osd'],
                'slave-03': ['controller', 'ceph-osd'],
                'slave-04': ['controller', 'ceph-osd'],
                'slave-05': ['compute', 'cinder', 'ceph-osd'],
                'slave-06': ['compute', 'cinder', 'ceph-osd'],
                'slave-07': ['compute', 'cinder', 'ceph-osd'],
                'slave-08': ['compute', 'cinder', 'ceph-osd'],
                'slave-09': ['compute', 'cinder', 'ceph-osd']
            }
        )
        # Cluster deploy
        self.fuel_web.deploy_cluster_wait(cluster_id,
                                          timeout=120 * 60,
                                          interval=30)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Check stack autoscaling'])

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_release],
          groups=["nine_nodes_separate_roles"])
    @log_snapshot_on_error
    def nine_nodes_separate_roles(self):
        """Deploy cluster with separate roles on 9 nodes in HA mode with GRE

        Scenario:
            1. Create cluster
            2. Add 3 nodes as controllers
            3. Add 2 nodes as compute
            4. Add 2 nodes as cinder
            5. Add 2 nodes as ceph
            6. Turn on Savanna and Ceilometer
            7. Deploy the cluster
            8. Check networks and OSTF

        Snapshot None

        """
        if settings.OPENSTACK_RELEASE == settings.OPENSTACK_RELEASE_REDHAT:
            raise SkipTest()

        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(self.env.nodes().slaves[:9])

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings={
                'volumes_ceph': True,
                'images_ceph': True,
                'sahara': True,
                'ceilometer': True,
                'net_provider': 'neutron',
                'net_segment_type': 'gre'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['controller'],
                'slave-05': ['compute'],
                'slave-06': ['cinder'],
                'slave-07': ['cinder'],
                'slave-08': ['ceph'],
                'slave-09': ['ceph'],
            }
        )
        # Cluster deploy
        self.fuel_web.deploy_cluster_wait(cluster_id,
                                          timeout=120 * 60,
                                          interval=30)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=1)
