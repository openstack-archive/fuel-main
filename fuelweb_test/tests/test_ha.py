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


@test
class TestHaVLAN(TestBasic):

    @test(
        groups=["thread_3", "ha"],
        depends_on=[SetupEnvironment.prepare_slaves_5])
    @log_snapshot_on_error
    def deploy_ha_vlan(self):
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

    @test(groups=["thread_3", "ha"], depends_on=[deploy_ha_vlan])
    @log_snapshot_on_error
    def deploy_ha_vlan_verify_networks(self):
        self.env.revert_snapshot("deploy_ha_vlan")

        #self.env.get_ebtables(self.fuel_web.get_last_created_cluster(),
        #                      self.env.nodes().slaves[:2]).restore_vlans()
        task = self.fuel_web.run_network_verify(
            self.fuel_web.get_last_created_cluster())
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

    @test(groups=["thread_3", "ha"], depends_on=[deploy_ha_vlan])
    @log_snapshot_on_error
    def deploy_ha_vlan_ostf(self):
        self.env.revert_snapshot("deploy_ha_vlan")

        self.run_OSTF(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=4, should_pass=24
        )


@test
class TestHaFlat(TestBasic):

    @test(
        groups=["thread_4", "ha"],
        depends_on=[SetupEnvironment.prepare_slaves_5])
    @log_snapshot_on_error
    def deploy_ha_flat(self):
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

    @test(groups=["thread_4", "ha"], depends_on=[deploy_ha_flat])
    @log_snapshot_on_error
    def deploy_ha_flat_verify_networks(self):
        self.env.revert_snapshot("deploy_ha_flat")

        task = self.fuel_web.run_network_verify(
            self.fuel_web.get_last_created_cluster())
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

    @test(groups=["thread_4", "ha"], depends_on=[deploy_ha_flat])
    @log_snapshot_on_error
    def deploy_ha_flat_ostf(self):
        self.env.revert_snapshot("deploy_ha_flat")

        self.run_OSTF(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=4, should_pass=24
        )


@test
class TestHaFlatAddCompute(TestBasic):

    @test(groups=["thread_4", "ha"], depends_on=[TestHaFlat.deploy_ha_flat])
    @log_snapshot_on_error
    def ha_flat_add_compute(self):
        self.env.revert_snapshot("deploy_ha_flat")

        self.env.bootstrap_nodes(self.nodes().slaves[5:6])
        cluster_id = self.fuel_web.get_last_created_cluster()
        self.fuel_web.update_nodes(
            cluster_id, {'slave-06': ['compute']}, True, False
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.env.make_snapshot("ha_flat_add_compute")

    @test(groups=["thread_4", "ha"], depends_on=[ha_flat_add_compute])
    @log_snapshot_on_error
    def ha_flat_add_compute_verify_networks(self):
        self.env.revert_snapshot("ha_flat_add_compute")

        task = self.fuel_web.run_network_verify(
            self.fuel_web.get_last_created_cluster())
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

    @test(groups=["thread_4", "ha"], depends_on=[ha_flat_add_compute])
    @log_snapshot_on_error
    def ha_flat_add_compute_ostf(self):
        self.env.revert_snapshot("ha_flat_add_compute")

        self.run_OSTF(
            cluster_id=self.fuel_web.get_last_created_cluster(),
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=4, should_pass=24
        )
