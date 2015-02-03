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


from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings as hlp_date
from fuelweb_test.tests import base_test_case


@test(groups=["ostf_repeatable_tests"])
class OstfRepeatableTests(base_test_case.TestBasic):

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_3],
          groups=["create_delete_ip_n_times_nova_vlan"])
    @log_snapshot_on_error
    def create_delete_ip_n_times_nova_vlan(self):
        """Deploy cluster in ha mode with VLAN Manager

        Scenario:
            1. Create cluster in ha mode with 1 controller
            2. Add 1 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Set up cluster to use Network VLAN manager with 8 networks
            5. Deploy the cluster
            6. Run network verification
            7. Run test Check network connectivity
               from instance via floating IP' n times

        Duration 1000m
        Snapshot create_delete_ip_n_times_nova_vlan

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_date.DEPLOYMENT_MODE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.update_vlan_network_fixed(
            cluster_id, amount=8, network_size=32)
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf_repeatably(cluster_id)

        self.env.make_snapshot("create_delete_ip_n_times_nova_vlan")

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_3],
          groups=["create_delete_ip_n_times_nova_flat"])
    @log_snapshot_on_error
    def deploy_create_delete_ip_n_times_nova_flat(self):
        """Deploy HA cluster, check connectivity from instance n times

        Scenario:
            1. Create cluster in ha mode with 1 controller
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy the cluster
            5. Verify networks
            6. Run test Check network connectivity
               from instance via floating IP' n times

        Duration 1000m
        Snapshot: create_delete_ip_n_times_nova_flat

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_date.DEPLOYMENT_MODE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.fuel_web.verify_network(cluster_id)
        self.fuel_web.run_ostf_repeatably(cluster_id)

        self.env.make_snapshot("create_delete_ip_n_times_nova_flat")

    @test(groups=["run_ostf_n_times_against_custom_environment"])
    @log_snapshot_on_error
    def run_ostf_n_times_against_custom_deployment(self):
        cluster_id = self.fuel_web.client.get_cluster_id(
            hlp_date.DEPLOYMENT_NAME)
        self.fuel_web.run_ostf_repeatably(cluster_id)
