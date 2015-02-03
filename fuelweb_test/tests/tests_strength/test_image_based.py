#    Copyright 2015 Mirantis, Inc.
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

from devops.helpers.helpers import wait
from proboscis import test

from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.settings import DEPLOYMENT_MODE
from fuelweb_test.tests.base_test_case import SetupEnvironment
from fuelweb_test.tests.base_test_case import TestBasic


@test(groups=["repeatable_image_based", "image_based"])
class RepeatableImageBased(TestBasic):

    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["repeatable_image_based", "image_based"])
    @log_snapshot_on_error
    def repeatable_image_based(self):
        """Provision new cluster many times after deletion the old one

        Scenario:
            1. Create HA cluster
            2. Add 1 controller, 2 compute and 2 cinder nodes
            3. Deploy the cluster
            4. Delete cluster
            5. Create another HA cluster
            6. Create snapshot of environment
            7. Revert snapshot and try provision cluster 10 times

        Duration 60m

        """
        self.env.revert_snapshot("ready_with_5_slaves")
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": 'gre'})
        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': ['controller'],
                'slave-02': ['compute'],
                'slave-03': ['compute'],
                'slave-04': ['cinder'],
                'slave-05': ['cinder']
            }
        )
        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.client.delete_cluster(cluster_id)
        #wait nodes go to reboot
        wait(lambda: not self.fuel_web.client.list_nodes(), timeout=5 * 60)
        #wait for nodes to appear after bootstrap
        wait(lambda: len(self.fuel_web.client.list_nodes()) == 5,
             timeout=5 * 60)
        for node in self.fuel_web.client.list_nodes():
            wait(lambda: self.fuel_web.is_node_discovered(node),
                 timeout=2 * 60)
        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": 'vlan'
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

        self.env.make_snapshot("deploy_after_delete", is_make=True)

        for i in range(0, 10):
            self.env.revert_snapshot("deploy_after_delete")
            cluster_id = self.fuel_web.get_last_created_cluster()
            self.fuel_web.provisioning_cluster_wait(cluster_id)
