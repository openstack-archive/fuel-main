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

from proboscis.asserts import assert_equal
from proboscis import test

from fuelweb_test import logger as LOGGER
from fuelweb_test.helpers import checkers
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.helpers import os_actions
from fuelweb_test.settings import DEPLOYMENT_MODE_HA
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["scale_ha", "scale_ha_neutron_gre"])
class ScaleNeutronGreHaCephCeilo(TestBasic):

    @test(depends_on=[SetupEnvironment.ready_with_10_slaves],
          groups=["deploy_scale_neutron_gre_ha_ceph_ceilo",
                  "scale_ha_neutron_gre"])
    @log_snapshot_on_error
    def deploy_neutron_gre_ha(self):
        """Deploy cluster in HA mode with Neutron GRE

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller and ceph role
            3. Add 6 nodes with compute and ceph roles
            4. Add 1 nodes with compute and mongo roles
            5. Deploy the cluster
            6. Verify smiles count
            7. Verify ceilometer api is running

        Snapshot deploy_scale_neutron_gre_ha_ceph_ceilo

        """
        self.env.revert_snapshot("ready_with_10_slaves")

        data = {
            'ceilometer': True,
            'net_provider': 'neutron',
            'net_segment_type': 'gre',
            'tenant': 'haGreCephScale',
            'user': 'haGreCephScale',
            'password': 'haGreCephScale'
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
                'slave-09': ['compute', 'ceph-osd'],
                'slave-10': ['mongo'],
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
                os_conn, smiles_count=18, networks_count=2, timeout=300)

        partitions = checkers.get_mongo_partitions(
            self.env.get_ssh_to_remote_by_name("slave-10"), "vda5")
        assert_equal(partitions[0].rstrip(), mongo_disk_gb,
                     'Mongo size {0} before deployment is not equal'
                     ' to size after {1}'.format(mongo_disk_gb, partitions))

        self.env.make_snapshot("deploy_scale_neutron_gre_ha_ceph_ceilo")


@test(groups=["scale_ha", "scale_ha_neutron_vlan"])
class ScaleNeutronVlanHaCephCeilo(TestBasic):

    @test(depends_on=[SetupEnvironment.ready_with_10_slaves],
          groups=["deploy_scale_neutron_vlan_ha_ceph_ceilo",
                  "scale_ha_neutron_vlan"])
    @log_snapshot_on_error
    def deploy_neutron_gre_ha(self):
        """Deploy cluster in HA mode with Neutron VLAN

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller and ceph role
            3. Add 6 nodes with compute and ceph roles
            4. Add 1 nodes with mongo roles
            5. Deploy the cluster
            6. Verify smiles count
            7. Verify ceilometer api is running

        Snapshot deploy_scale_neutron_gre_ha_ceph_ceilo

        """
        self.env.revert_snapshot("ready_with_10_slaves")

        data = {
            'ceilometer': True,
            'net_provider': 'neutron',
            'net_segment_type': 'vlan',
            'tenant': 'haGreCephScale',
            'user': 'haGreCephScale',
            'password': 'haGreCephScale'
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
                'slave-09': ['compute', 'ceph-osd'],
                'slave-10': ['mongo'],
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
                os_conn, smiles_count=18, networks_count=2, timeout=300)

        partitions = checkers.get_mongo_partitions(
            self.env.get_ssh_to_remote_by_name("slave-10"), "vda5")
        assert_equal(partitions[0].rstrip(), mongo_disk_gb,
                     'Mongo size {0} before deployment is not equal'
                     ' to size after {1}'.format(mongo_disk_gb, partitions))

        self.env.make_snapshot("deploy_scale_neutron_vlan_ha_ceph_ceilo")
