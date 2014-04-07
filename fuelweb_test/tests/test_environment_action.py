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

from proboscis import asserts
from proboscis import SkipTest
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings as hlp_data
from fuelweb_test import logger
from fuelweb_test.tests import base_test_case


@test(groups=["thread_2", "cluster_actions"])
class EnvironmentAction(base_test_case.TestBasic):

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_3],
          groups=["smoke", "deploy_flat_stop_reset_on_deploying"])
    @log_snapshot_on_error
    def deploy_flat_stop_on_deploying(self):
        """Stop reset cluster in simple mode with flat nova-network

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Run provisioning task
            5. Run deployment task
            6. Stop deployment
            7. Add 1 node with cinder role
            8. Re-deploy cluster
            9. Run OSTF

        Snapshot: deploy_flat_stop_reset_on_deploying

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_data.DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )

        self.fuel_web.provisioning_cluster_wait(cluster_id)
        self.fuel_web.deploy_task_wait(cluster_id=cluster_id, progress=10)
        self.fuel_web.stop_deployment_wait(cluster_id)
        self.fuel_web.wait_nodes_get_online_state(self.env.nodes().slaves[:2])

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-03': ['cinder']
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)

        asserts.assert_equal(
            3, len(self.fuel_web.client.list_cluster_nodes(cluster_id)))

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=0)

        self.env.make_snapshot("deploy_flat_stop_reset_on_deploying")

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_3],
          groups=["smoke", "deploy_flat_stop_reset_on_provisioning"])
    @log_snapshot_on_error
    def deploy_flat_stop_reset_on_provisioning(self):
        """Stop reset cluster in simple mode with flat nova-network

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Run provisioning task
            5. Stop deployment
            6. Reset settings
            7. Add 1 node with cinder role
            8. Re-deploy cluster
            9. Run OSTF

        Snapshot: deploy_flat_stop_reset_on_deploying

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_data.DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )

        self.fuel_web.provisioning_cluster_wait(
            cluster_id=cluster_id, progress=20)
        try:
            self.fuel_web.stop_deployment_wait(cluster_id)
        except Exception as e:
            logger.debug('current massage is {0}'.format(e.read()))
            logger.debug('code is {0}'.format(e.code))

            if e.code == 400:
                logger.debug('try to skip tests - feature is not implemented')
                raise SkipTest(e.read())
            else:
                raise e
        self.fuel_web.wait_nodes_get_online_state(self.env.nodes().slaves[:2])
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-03': ['cinder']
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)

        asserts.assert_equal(
            3, len(self.fuel_web.client.list_cluster_nodes(cluster_id)))

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=0)

        self.env.make_snapshot("deploy_flat_stop_reset_on_provisioning")

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_3],
          groups=["smoke", "deploy_reset_on_ready"])
    @log_snapshot_on_error
    def deploy_reset_on_ready(self):
        """Stop reset cluster in simple mode

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy cluster
            5. Reset settings
            6. Update net
            7. Re-deploy cluster
            8. Run OSTF

        Snapshot: deploy_reset_on_ready

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_data.DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=1, timeout=300)

        self.fuel_web.stop_reset_env_wait(cluster_id)
        self.fuel_web.wait_nodes_get_online_state(self.env.nodes().slaves[:2])

        self.fuel_web.update_vlan_network_fixed(
            cluster_id, amount=8, network_size=32)
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=6, networks_count=8, timeout=300)

        task = self.fuel_web.run_network_verify(cluster_id)
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])

        self.env.make_snapshot("deploy_reset_on_ready")


@test(groups=["thread_3", "cluster_actions"])
class EnvironmentActionOnHA(base_test_case.TestBasic):

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_5],
          groups=["smoke", "deploy_stop_reset_on_ha"])
    @log_snapshot_on_error
    def deploy_stop_reset_on_ha(self):
        """Stop reset cluster in ha mode

        Scenario:
            1. Create cluster
            2. Add 3 node with controller role
            3. Deploy cluster
            4. Stop deployment
            5. Reset settings
            6. Add 2 nodes with compute role
            7. Re-deploy cluster
            8. Run OSTF

        Snapshot: deploy_stop_reset_on_ha

        """
        self.env.revert_snapshot("ready_with_5_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_data.DEPLOYMENT_MODE_HA

        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['controller'],
                'slave-03': ['controller']
            }
        )

        self.fuel_web.deploy_cluster_wait_progress(cluster_id, progress=10)
        self.fuel_web.stop_deployment_wait(cluster_id)
        self.fuel_web.wait_nodes_get_online_state(self.env.nodes().slaves[:3])
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-04': ['compute'],
                'slave-05': ['compute']
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.assert_cluster_ready(
            'slave-01', smiles_count=16, networks_count=1, timeout=300)

        self.fuel_web.verify_network(cluster_id)

        self.fuel_web.run_ostf(
            cluster_id=cluster_id,
            test_sets=['ha', 'smoke', 'sanity'],
            should_fail=1,
            failed_test_name=['Create volume and attach it to instance'])

        self.env.make_snapshot("deploy_stop_reset_on_ha")
