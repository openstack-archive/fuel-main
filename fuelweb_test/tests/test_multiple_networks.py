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
from proboscis.asserts import assert_equal

from fuelweb_test import logger
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.settings import DEPLOYMENT_MODE_HA
from fuelweb_test.settings import MULTIPLE_NETWORKS
from fuelweb_test.settings import NODEGROUPS
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test.tests.base_test_case import SetupEnvironment


@test(groups=["multiple_cluster_networks"])
class TestMultipleClusterNets(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["multiple_cluster_net_setup"])
    @log_snapshot_on_error
    @test(groups=["multiple_cluster_net_setup"])
    def multiple_cluster_net_setup(self):
        """Check master node deployment and configuration with 2 sets of nets

        Scenario:
            1. Revert snapshot with 5 slaves
            2. Check that slave nodes got addresses from both L2 networks
            3. Create HA cluster with Neutron GRE
            4. Add 3 controller nodes from default nodegroup
            5. Add 2 compute nodes from custom nodegroup
            6. Deploy cluster
            7. Run health checks

        Snapshot multiple_cluster_net_setup

        """

        if not MULTIPLE_NETWORKS:
            raise SkipTest()
        self.env.revert_snapshot("ready_with_5_slaves")

        networks = ['.'.join(self.env.get_network(n).split('.')[0:-1]) for n
                    in [self.env.admin_net, self.env.admin_net2]]

        nodes_addresses = []
        for node in self.fuel_web.client.list_nodes():
            nodes_addresses.append('.'.join(node['ip'].split('.')[0:-1]))
        assert_equal(set(networks), set(nodes_addresses),
                     "Only one admin network is used for discovering slaves:"
                     " '{0}'".format(set(nodes_addresses)))

        cluster_id = self.fuel_web.create_cluster(
            name=self.__class__.__name__,
            mode=DEPLOYMENT_MODE_HA,
            settings={
                "net_provider": 'neutron',
                "net_segment_type": 'gre',
                'tenant': 'haGre',
                'user': 'haGre',
                'password': 'haGre'
            }
        )

        nodegroup1 = NODEGROUPS[0]['name']
        nodegroup2 = NODEGROUPS[1]['name']

        self.fuel_web.update_nodes(
            cluster_id,
            {
                'slave-01': [['controller'], nodegroup1],
                'slave-05': [['controller'], nodegroup1],
                'slave-03': [['controller'], nodegroup1],
                'slave-02': [['compute'], nodegroup2],
                'slave-04': [['compute'], nodegroup2],
            }
        )

        self.fuel_web.deploy_cluster_wait(cluster_id)
        self.fuel_web.run_ostf(cluster_id=cluster_id)
        self.env.make_snapshot("multiple_cluster_net_setup")
