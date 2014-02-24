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

from proboscis import asserts
from proboscis import test

from fuelweb_test.helpers.decorators import debug
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test import settings as hlp_date
from fuelweb_test.tests import base_test_case

logger = logging.getLogger(__name__)
logwrap = debug(logger)


@test(groups=["thread_5"])
class FloatingIpActions(base_test_case.TestBasic):
    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_3],
          groups=["create_delete_ip_50_times_nova_vlan"])
    @log_snapshot_on_error
    def create_delete_ip_50_times_nova_vlan(self):
        """Deploy cluster in simple mode with VLAN Manager

        Scenario:
            1. Create cluster
            2. Add 1 nodes with controller roles
            3. Add 2 nodes with compute roles
            4. Set up cluster to use Network VLAN manager with 8 networks
            5. Deploy the cluster
            6. Run network verification
            7. Run test Check network connectivity
               from instance via floating IP' 50times

        Snapshot create_delete_ip_50_times_nova_vlan

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_date.DEPLOYMENT_MODE_SIMPLE
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
        res = []
        passed_count = []
        failed_count = []
        d_key = 'Check network connectivity from instance via floating IP'

        for i in range(0, 51):
            result = self.fuel_web.run_single_ostf_test(
                cluster_id=cluster_id, test_sets=['smoke'],
                test_name=('fuel_health.tests.smoke.test_nova_create_instance_'
                           'with_connectivity.TestNovaNetwork.test_008_check_'
                           'public_instance_connectivity_from_instance'),
                retries=True)
            res.append(result)
            logger.info('res is {0}'.format(res))

        for element in res:
            [passed_count.append(test)
             for test in element if test[d_key] == 'success']
            [failed_count.append(test)
             for test in element if (test[d_key] == 'failure' or 'error')]

        asserts.assert_true(len(passed_count) == 50,
                            'not all retries were successful, '
                            'fail {0} retries'.format(len(failed_count)))

        self.env.make_snapshot("create_delete_ip_50_times_nova_vlan")

    @test(depends_on=[base_test_case.SetupEnvironment.prepare_slaves_3],
          groups=["create_delete_ip_50_times_nova_flat"])
    @log_snapshot_on_error
    def deploy_create_delete_ip_50_times_nova_flat(self):
        """Deploy cluster in simple mode with flat nova-network

        Scenario:
            1. Create cluster
            2. Add 1 node with controller role
            3. Add 1 node with compute role
            4. Deploy the cluster
            5. Verify networks
            6. Run test Check network connectivity
               from instance via floating IP' 50times

        Snapshot: create_delete_ip_50_times_nova_flat

        """
        self.env.revert_snapshot("ready_with_3_slaves")

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=hlp_date.DEPLOYMENT_MODE_SIMPLE
        )
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)

        task = self.fuel_web.run_network_verify(cluster_id)
        self.fuel_web.assert_task_success(task, 60 * 2, interval=10)

        res = []
        d_key = 'Check network connectivity from instance via floating IP'
        passed_count = []
        failed_count = []

        for i in range(0, 51):
            result = self.fuel_web.run_single_ostf_test(
                cluster_id=cluster_id, test_sets=['smoke'],
                test_name=('fuel_health.tests.smoke.test_nova_create_instance_'
                           'with_connectivity.TestNovaNetwork.test_008_check_'
                           'public_instance_connectivity_from_instance'),
                retries=True)
            res.append(result)
            logger.info('res is {0}'.format(res))

        for element in res:
            [passed_count.append(test)
             for test in element if test[d_key] == 'success']
            [failed_count.append(test)
             for test in element if (test[d_key] == 'failure' or 'error')]

        asserts.assert_true(len(passed_count) == 50,
                            'not all retries were successful, '
                            'fail {0} retries'.format(len(failed_count)))

        self.env.make_snapshot("create_delete_ip_50_times_nova_flat")
