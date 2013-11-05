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
from proboscis import test

from fuelweb_test.helpers.decorators import debug, log_snapshot_on_error
from fuelweb_test.models.fuel_web_client import DEPLOYMENT_MODE_HA
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test(groups=["thread_3", "ha"])
class TestHaVLAN(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_ha_vlan"])
    @log_snapshot_on_error
    def deploy_ha_vlan(self):
        """Deploy cluster in HA mode with VLAN Manager

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Set up cluster to use Network VLAN manager with 8 networks
            5. Deploy the cluster
            6. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs

        Snapshot: deploy_ha_vlan

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA
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
        self.fuel_web.update_vlan_network_fixed(
            cluster_id, amount=8, network_size=32
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.assertClusterReady(
            'slave-01', smiles_count=16, networks_count=8, timeout=300)
        self.env.make_snapshot("deploy_ha_vlan")

    @test(depends_on=[deploy_ha_vlan],
          groups=["deploy_ha_vlan_verify_networks"])
    @log_snapshot_on_error
    def deploy_ha_vlan_verify_networks(self):
        """Verify network on cluster in HA mode with VLAN Manager

        Scenario:
            1. Revert snapshot "deploy_ha_vlan"
            2. Run network verification

        """
        self.env.revert_snapshot("deploy_ha_vlan")

        #self.env.get_ebtables(self.fuel_web.get_last_created_cluster(),
        #                      self.env.nodes().slaves[:2]).restore_vlans()
        self.fuel_web.verify_network(self.fuel_web.get_last_created_cluster())

    @test(depends_on=[deploy_ha_vlan],
          groups=["revert_snapshot"])
    @log_snapshot_on_error
    def deploy_ha_vlan_ostf(self):
        """Run OSTF tests on cluster in HA mode with VLAN Manager

        Scenario:
            1. Revert snapshot "deploy_ha_vlan"
            2. Run OSTF

        """
        self.env.revert_snapshot("deploy_ha_vlan")

        self.run_OSTF(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=4, should_pass=24
        )


@test(groups=["thread_4", "ha"])
class TestHaFlat(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["deploy_ha_flat"])
    @log_snapshot_on_error
    def deploy_ha_flat(self):
        """Deploy cluster in HA mode with flat nova-network

        Scenario:
            1. Create cluster
            2. Add 3 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Deploy the cluster
            5. Validate cluster was set up correctly, there are no dead
            services, there are no errors in logs

        Snapshot: deploy_ha_flat

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA
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
        self.assertClusterReady(
            'slave-01', smiles_count=16, networks_count=8, timeout=300)
        self.env.make_snapshot("deploy_ha_flat")

    @test(depends_on=[deploy_ha_flat],
          groups=["deploy_ha_flat_verify_networks"])
    @log_snapshot_on_error
    def deploy_ha_flat_verify_networks(self):
        """Verify network on cluster in HA mode with flat nova-network

        Scenario:
            1. Revert snapshot "deploy_ha_flat"
            2. Run network verification

        """
        self.env.revert_snapshot("deploy_ha_flat")

        self.fuel_web.verify_network(self.fuel_web.get_last_created_cluster())

    @test(depends_on=[deploy_ha_flat],
          groups=["deploy_ha_flat_ostf"])
    @log_snapshot_on_error
    def deploy_ha_flat_ostf(self):
        """Run OSTF tests on cluster in HA mode with flat nova-network

        Scenario:
            1. Revert snapshot "deploy_ha_flat"
            2. Run OSTF

        """
        self.env.revert_snapshot("deploy_ha_flat")

        self.run_OSTF(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=4, should_pass=24
        )


@test(groups=["thread_4", "ha"])
class TestHaFlatAddCompute(TestBasic):

    @test(depends_on=[TestHaFlat.deploy_ha_flat],
          groups=["ha_flat_add_compute"])
    @log_snapshot_on_error
    def ha_flat_add_compute(self):
        """Add compute node to cluster in HA mode with flat nova-network

        Scenario:
            1. Revert snapshot "deploy_ha_flat"
            2. Add 1 node with compute role
            3. Deploy the cluster

        Snapshot: ha_flat_add_compute

        """
        self.env.revert_snapshot("deploy_ha_flat")

        self.env.bootstrap_nodes(self.nodes().slaves[5:6])
        cluster_id = self.fuel_web.get_last_created_cluster()
        self.fuel_web.update_nodes(
            cluster_id, {'slave-06': ['compute']}, True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.env.make_snapshot("ha_flat_add_compute")

    @test(depends_on=[ha_flat_add_compute],
          groups=["ha_flat_add_compute_verify_networks"])
    @log_snapshot_on_error
    def ha_flat_add_compute_verify_networks(self):
        """Verify network on cluster in HA mode after add compute node

        Scenario:
            1. Revert snapshot "ha_flat_add_compute"
            2. Run network verification

        """
        self.env.revert_snapshot("ha_flat_add_compute")
        self.fuel_web.verify_network(self.fuel_web.get_last_created_cluster())

    @test(depends_on=[ha_flat_add_compute],
          groups=["ha_flat_add_compute_ostf"])
    @log_snapshot_on_error
    def ha_flat_add_compute_ostf(self):
        """Run OSTF tests on cluster in HA mode after add compute node

        Scenario:
            1. Revert snapshot "ha_flat_add_compute"
            2. Run OSTF

        """
        self.env.revert_snapshot("ha_flat_add_compute")

        self.run_OSTF(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=4, should_pass=24
        )
