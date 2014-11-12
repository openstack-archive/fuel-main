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

from proboscis.asserts import assert_equal
from proboscis import test
from proboscis import SkipTest

from fuelweb_test import logger as LOGGER
from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings
from fuelweb_test.tests import base_test_case
from fuelweb_test.helpers import os_actions
from fuelweb_test.settings import DEPLOYMENT_MODE_HA
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


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
class HugeHaNeutron(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_9],
          groups=["huge_ha_neutron_ceph_ceilo",
                  "huge_ha_neutron_gre_ceph_ceilo"])
    @log_snapshot_on_error
    def deploy_neutron_gre_ha_ceph_ceilo(self):
        """Deploy cluster in HA mode with Neutron GRE

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller and ceph role
            3. Add 5 nodes with compute and ceph roles
            4. Add 1 nodes with compute and mongo roles
            5. Deploy the cluster
            6. Verify smiles count
            7. Verify ceilometer api is running

        Snapshot deploy_scale_neutron_gre_ha_ceph_ceilo

        """
        self.env.revert_snapshot("ready_with_9_slaves")

        data = {
            'ceilometer': True,
            'volumes_ceph': True,
            'images_ceph': True,
            'volumes_lvm': False,
            'net_provider': 'neutron',
            'net_segment_type': 'gre',
            'tenant': 'haGreCephHugeScale',
            'user': 'haGreCephHugeScale',
            'password': 'haGreCephHugeScale'
        }

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
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
                'slave-07': ['compute', 'ceph-osd'],
                'slave-08': ['compute', 'ceph-osd'],
                'slave-09': ['mongo'],
            }
        )
        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)

        disk_mb = 0
        for node in nailgun_nodes:
            if node.get('pending_roles') == ['mongo']:
                disk_mb = self.fuel_web.get_node_disk_size(node.get('id'),
                                                           "vda")

        LOGGER.debug('disk size is {0}'.format(disk_mb))
        mongo_disk_mb = 11116
        os_disk_mb = disk_mb - mongo_disk_mb
        mongo_disk_gb = ("{0}G".format(round(mongo_disk_mb / 1024, 1)))
        disk_part = {
            "vda": {
                "os": os_disk_mb,
                "mongo": mongo_disk_mb
            }
        }

        for node in nailgun_nodes:
            if node.get('pending_roles') == ['mongo']:
                self.fuel_web.update_node_disk(node.get('id'), disk_part)

        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        # assert_equal(str(cluster['net_segment_type']), segment_type)

        for controller in ('slave-01', 'slave-02', 'slave-03'):
            checkers.verify_service(
                self.env.get_ssh_to_remote_by_name(controller),
                service_name='ceilometer-api')
            os_conn = os_actions.OpenStackActions(
                controller['ip'],
                data['user'],
                data['password'],
                data['tenant'])
            self.fuel_web.assert_cluster_ready(
                os_conn, smiles_count=17, networks_count=2, timeout=300)

        partitions = checkers.get_mongo_partitions(
            self.env.get_ssh_to_remote_by_name("slave-09"), "vda5")
        assert_equal(partitions[0].rstrip(), mongo_disk_gb,
                     'Mongo size {0} before deployment is not equal'
                     ' to size after {1}'.format(mongo_disk_gb, partitions))

        self.env.make_snapshot("deploy_scale_neutron_gre_ha_ceph_ceilo")

    @test(depends_on=[SetupEnvironment.prepare_slaves_9],
          groups=["huge_ha_neutron_ceph_ceilo",
                  "huge_ha_neutron_vlan_ceph_ceilo"])
    @log_snapshot_on_error
    def deploy_neutron_vlan_ha_ceph_ceilo(self):
        """Deploy cluster in HA mode with Neutron VLAN

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller and ceph role
            3. Add 5 nodes with compute and ceph roles
            4. Add 1 nodes with mongo roles
            5. Deploy the cluster
            6. Verify smiles count
            7. Verify ceilometer api is running

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
            mode=DEPLOYMENT_MODE_HA,
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
                'slave-07': ['compute', 'ceph-osd'],
                'slave-08': ['compute', 'ceph-osd'],
                'slave-09': ['mongo'],
            }
        )
        nailgun_nodes = self.fuel_web.client.list_cluster_nodes(cluster_id)

        disk_mb = 0
        for node in nailgun_nodes:
            if node.get('pending_roles') == ['mongo']:
                disk_mb = self.fuel_web.get_node_disk_size(node.get('id'),
                                                           "vda")

        LOGGER.debug('disk size is {0}'.format(disk_mb))
        mongo_disk_mb = 11116
        os_disk_mb = disk_mb - mongo_disk_mb
        mongo_disk_gb = ("{0}G".format(round(mongo_disk_mb / 1024, 1)))
        disk_part = {
            "vda": {
                "os": os_disk_mb,
                "mongo": mongo_disk_mb
            }
        }

        for node in nailgun_nodes:
            if node.get('pending_roles') == ['mongo']:
                self.fuel_web.update_node_disk(node.get('id'), disk_part)

        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        # assert_equal(str(cluster['net_segment_type']), segment_type)

        for controller in ('slave-01', 'slave-02', 'slave-03'):
            checkers.verify_service(
                self.env.get_ssh_to_remote_by_name(controller),
                service_name='ceilometer-api')
            os_conn = os_actions.OpenStackActions(
                controller['ip'],
                data['user'],
                data['password'],
                data['tenant'])
            self.fuel_web.assert_cluster_ready(
                os_conn, smiles_count=17, networks_count=2, timeout=300)

        partitions = checkers.get_mongo_partitions(
            self.env.get_ssh_to_remote_by_name("slave-09"), "vda5")
        assert_equal(partitions[0].rstrip(), mongo_disk_gb,
                     'Mongo size {0} before deployment is not equal'
                     ' to size after {1}'.format(mongo_disk_gb, partitions))
