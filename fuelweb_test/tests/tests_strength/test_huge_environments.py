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
from fuelweb_test import ostf_test_mapping as map_ostf
from fuelweb_test.tests import base_test_case
from fuelweb_test.helpers import os_actions


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
            3. Add 5 nodes as compute with ceph OSD and mongo roles
            4. Turn on Sahara and Ceilometer
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
                'volumes_lvm': False,
                'sahara': True,
                'ceilometer': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'mongo'],
                'slave-02': ['controller', 'mongo'],
                'slave-03': ['controller', 'mongo'],
                'slave-04': ['controller', 'mongo'],
                'slave-05': ['compute', 'ceph-osd'],
                'slave-06': ['compute', 'ceph-osd'],
                'slave-07': ['compute', 'ceph-osd'],
                'slave-08': ['compute', 'ceph-osd'],
                'slave-09': ['compute', 'ceph-osd']
            }
        )
        # Cluster deploy
        self.fuel_web.deploy_cluster_wait(cluster_id,
                                          timeout=120 * 60,
                                          interval=30)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_release],
          groups=["nine_nodes_separate_roles"])
    @log_snapshot_on_error
    def nine_nodes_separate_roles(self):
        """Deploy cluster with separate roles on 9 nodes in HA mode with GRE

        Scenario:
            1. Create cluster
            2. Add 3 nodes as controllers
            3. Add 2 nodes as compute
            4. Add 1 node as cinder and 1 as mongo
            5. Add 2 nodes as ceph
            6. Turn on Sahara and Ceilometer
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
                'images_ceph': False,
                'volumes_lvm': False,
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
                'slave-04': ['compute'],
                'slave-05': ['compute'],
                'slave-06': ['cinder'],
                'slave-07': ['mongo'],
                'slave-08': ['ceph-osd'],
                'slave-09': ['ceph-osd'],
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


@test(groups=["huge_environments", "huge_ha_neutron", "huge_scale"])
class HugeHaNeutron(base_test_case.TestBasic):

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_9],
          groups=["huge_ha_neutron_gre_ceph_ceilo_rados"])
    @log_snapshot_on_error
    def huge_ha_neutron_gre_ceph_ceilo_rados(self):
        """Deploy cluster in HA mode with Neutron GRE, RadosGW

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller and ceph role
            3. Add 3 nodes with compute and ceph roles
            4. Add 3 nodes with compute and mongo roles
            5. Deploy the cluster
            6. Verify smiles count
            7. Run OSTF

        Snapshot deploy_scale_neutron_gre_ha_ceph_ceilo

        """
        self.env.revert_snapshot("ready_with_9_slaves")

        data = {
            'volumes_lvm': False,
            'volumes_ceph': True,
            'images_ceph': True,
            'objects_ceph': True,
            'net_provider': 'neutron',
            'net_segment_type': 'gre',
            'tenant': 'haGreCephHugeScale',
            'user': 'haGreCephHugeScale',
            'password': 'haGreCephHugeScale'
        }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings=data
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'ceph-osd'],
                'slave-02': ['controller', 'ceph-osd'],
                'slave-03': ['controller', 'ceph-osd'],
                'slave-04': ['compute', 'ceph-osd'],
                'slave-05': ['compute', 'ceph-osd'],
                'slave-06': ['compute', 'ceph-osd'],
                'slave-07': ['mongo'],
                'slave-08': ['mongo'],
                'slave-09': ['mongo']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            data['user'],
            data['password'],
            data['tenant'])
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=14, networks_count=2, timeout=300)

        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.fuel_web.run_single_ostf_test(
            cluster_id=cluster_id, test_sets=['platform_tests'],
            test_name=map_ostf.OSTF_TEST_MAPPING.get(
                'Check stack autoscaling'))

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_9],
          groups=["huge_ha_neutron_vlan_ceph_ceilo_rados"])
    @log_snapshot_on_error
    def huge_ha_neutron_vlan_ceph_ceilo_rados(self):
        """Deploy cluster in HA mode with Neutron VLAN, RadosGW

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller and ceph role
            3. Add 3 nodes with compute and ceph roles
            4. Add 3 nodes with mongo roles
            5. Deploy the cluster
            6. Verify smiles count
            7. Run OSTF

        Snapshot None

        """
        self.env.revert_snapshot("ready_with_9_slaves")

        data = {
            'ceilometer': True,
            'volumes_ceph': True,
            'images_ceph': True,
            'volumes_lvm': False,
            'net_provider': 'neutron',
            'net_segment_type': 'vlan',
            'tenant': 'haVlanCephHugeScale',
            'user': 'haVlanCephHugeScale',
            'password': 'haVlanCephHugeScale'
        }
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=settings.DEPLOYMENT_MODE_HA,
            settings=data
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller', 'ceph-osd'],
                'slave-02': ['controller', 'ceph-osd'],
                'slave-03': ['controller', 'ceph-osd'],
                'slave-04': ['compute', 'ceph-osd'],
                'slave-05': ['compute', 'ceph-osd'],
                'slave-06': ['compute', 'ceph-osd'],
                'slave-07': ['mongo'],
                'slave-08': ['mongo'],
                'slave-09': ['mongo']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        os_conn = os_actions.OpenStackActions(
            self.fuel_web.get_public_vip(cluster_id),
            data['user'],
            data['password'],
            data['tenant'])
        self.fuel_web.assert_cluster_ready(
            os_conn, smiles_count=14, networks_count=2, timeout=300)

        self.fuel_web.run_ostf(cluster_id=cluster_id)

        self.fuel_web.run_single_ostf_test(
            cluster_id=cluster_id, test_sets=['platform_tests'],
            test_name=map_ostf.OSTF_TEST_MAPPING.get(
                'Check stack autoscaling'))
