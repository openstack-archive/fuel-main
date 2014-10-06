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

from fuelweb_test.settings import MULTIPLE_NETWORKS
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test.tests.base_test_case import SetupEnvironment


@test(groups=["multiple_cluster_networks"])
class TestMultipleClusterNets(TestBasic):
    @test(depends_on=[SetupEnvironment.prepare_slaves_5],
          groups=["multiple_cluster_net_setup"])
    @log_snapshot_on_error
    def multiple_cluster_net_setup(self):
        """Check master node deployment and configuration with 2 sets of nets

        Scenario:
            1. Revert snapshot with 5 slaves
            2. Check that slave nodes got addresses from both networks sets

        Snapshot multiple_cluster_net_setup

        """

        if not MULTIPLE_NETWORKS:
            raise SkipTest()
        self.env.revert_snapshot("ready_with_5_slaves")
        networks = [
        '.'.join(self.env.get_network(self.env.admin_net).split('.')[0:-1]),
         '.'.join(self.env.get_network(self.env.admin_net2).split('.')[0:-1])
        ]
        nodes_addresses = []
        for node in self.fuel_web.client.list_nodes():
            nodes_addresses.append('.'.join(node['ip'].split('.')[0:-1]))
        assert_equal(set(networks), set(nodes_addresses), ("Only one admin "
                     "network is used for slave nodes: '{0}'".format(
            set(nodes_addresses))))
        self.env.make_snapshot("multiple_cluster_net_setup")
