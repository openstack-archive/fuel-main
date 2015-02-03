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

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["thread_1", "neutron", "smoke_neutron"])
class NeutronGre(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_neutron_gre", "ha_one_controller_neutron_gre"])
    @log_snapshot_on_error
    def deploy_neutron_gre(self):
        """Deploy cluster in ha mode with 1 controller and Neutron GRE

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 2 nodes with compute role
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF

        Duration 35m
        Snapshot deploy_neutron_gre

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        segment_type = 'gre'
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type,
                'tenant': 'simpleGre',
                'user': 'simpleGre',
                'password': 'simpleGre'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute', 'cinder'],
                'slave-03': ['compute', 'cinder']
            }
        )
        self.fuel_web.update_internal_network(cluster_id, '192.168.196.0/26',
                                              '192.168.196.1')
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        # assert_equal(str(cluster['net_segment_type']), segment_type)
        self.fuel_web.check_fixed_network_cidr(
            cluster_id, self.env.get_ssh_to_remote_by_name('slave-01'))

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_neutron_gre")


@test(groups=["thread_1", "neutron"])
class NeutronVlan(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_3],
          groups=["deploy_neutron_vlan", "ha_one_controller_neutron_vlan"])
    @log_snapshot_on_error
    def deploy_neutron_vlan(self):
        """Deploy cluster in ha mode with 1 controller and Neutron VLAN

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 2 nodes with compute role
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF

        Duration 35m
        Snapshot deploy_neutron_vlan

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        segment_type = 'vlan'
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type,
                'tenant': 'simpleVlan',
                'user': 'simpleVlan',
                'password': 'simpleVlan'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        # assert_equal(str(cluster['net_segment_type']), segment_type)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_neutron_vlan")


@test(groups=["neutron", "ha", "ha_neutron", "image_based"])
class NeutronGreHa(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_neutron_gre_ha", "ha_neutron_gre"])
    @log_snapshot_on_error
    def deploy_neutron_gre_ha(self):
        """Deploy cluster in HA mode with Neutron GRE

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller role
            3. Add 2 nodes with compute role
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF

        Duration 80m
        Snapshot deploy_neutron_gre_ha

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        segment_type = 'gre'
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type,
                'tenant': 'haGre',
                'user': 'haGre',
                'password': 'haGre'
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_neutron_gre_ha")


@test(groups=["thread_6", "neutron", "ha", "ha_neutron"])
class NeutronGreHaPublicNetwork(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_neutron_gre_ha_public_network"])
    @log_snapshot_on_error
    def deploy_neutron_gre_ha_with_public_network(self):
        """Deploy cluster in HA mode with Neutron GRE and public network
           assigned to all nodes

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller role
            3. Add 2 nodes with compute role
            4. Enable assign public networks to all nodes option
            5. Deploy the cluster
            6. Check that public network was assigned to all nodes
            7. Run network verification
            8. Run OSTF

        Duration 80m
        Snapshot deploy_neutron_gre_ha_public_network

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        segment_type = 'gre'
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type,
                'tenant': 'haGre',
                'user': 'haGre',
                'password': 'haGre',
                'assign_to_all_nodes': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.security.verify_firewall(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_neutron_gre_ha_public_network")


@test(groups=["neutron", "ha", "ha_neutron"])
class NeutronVlanHa(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_neutron_vlan_ha", "ha_neutron_vlan"])
    @log_snapshot_on_error
    def deploy_neutron_vlan_ha(self):
        """Deploy cluster in HA mode with Neutron VLAN

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller role
            3. Add 2 nodes with compute role
            4. Deploy the cluster
            5. Run network verification
            6. Run OSTF

        Duration 80m
        Snapshot deploy_neutron_vlan_ha

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        segment_type = 'vlan'
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )
        self.fuel_web.update_internal_network(cluster_id, '192.168.196.0/22',
                                              '192.168.196.1')
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        # assert_equal(str(cluster['net_segment_type']), segment_type)
        self.fuel_web.check_fixed_network_cidr(
            cluster_id, self.env.get_ssh_to_remote_by_name('slave-01'))

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_neutron_vlan_ha")


@test(groups=["thread_6", "neutron", "ha", "ha_neutron"])
class NeutronVlanHaPublicNetwork(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_neutron_vlan_ha_public_network"])
    @log_snapshot_on_error
    def deploy_neutron_vlan_ha_with_public_network(self):
        """Deploy cluster in HA mode with Neutron VLAN and public network
           assigned to all nodes

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller role
            3. Add 2 nodes with compute role
            4. Enable assign public networks to all nodes option
            5. Deploy the cluster
            6. Check that public network was assigned to all nodes
            7. Run network verification
            8. Run OSTF

        Duration 80m
        Snapshot deploy_neutron_vlan_ha_public_network

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        segment_type = 'vlan'
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": segment_type,
                'assign_to_all_nodes': True
            }
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller'],
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )
        self.fuel_web.update_internal_network(cluster_id, '192.168.196.0/22',
                                              '192.168.196.1')
        self.fuel_web.deploy_cluster_wait(cluster_id)

        cluster = self.fuel_web.client.get_cluster(cluster_id)
        assert_equal(str(cluster['net_provider']), 'neutron')
        # assert_equal(str(cluster['net_segment_type']), segment_type)
        self.fuel_web.check_fixed_network_cidr(
            cluster_id, self.env.get_ssh_to_remote_by_name('slave-01'))

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.security.verify_firewall(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id)

        self.env.make_snapshot("deploy_neutron_vlan_ha_public_network")
