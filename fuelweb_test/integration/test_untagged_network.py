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
from fuelweb_test.integration.base_node_test_case import BaseNodeTestCase
from fuelweb_test.integration.decorators import snapshot_errors, \
    debug, fetch_logs
from time import sleep

logging.basicConfig(
    format=':%(lineno)d: %(asctime)s %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logwrap = debug(logger)


class TestUntaggedNetwork(BaseNodeTestCase):

    @snapshot_errors
    @logwrap
    @fetch_logs
    def test_untagged_network(self):
        cluster_name = 'simple_untagged'
        vlan_turn_off = {'vlan_start': None}
        nets_to_be_checked = ["public", "floating",
                              "management", "storage",
                              "fixed"]
        nodes = {
            'controller': ['slave-01'],
            'compute': ['slave-02'],
        }

        self.clean_clusters()

        # create a new empty cluster and add nodes to it:
        cluster_id = self.create_cluster(name=cluster_name)
        self.bootstrap_nodes(self.devops_nodes_by_names(
            nodes['controller']+nodes['compute']))
        self.update_nodes(cluster_id, nodes, True, False)

        # assign all networks to second network interface:
        nets = self.client.get_networks(cluster_id)['networks']
        for node in self.client.list_cluster_nodes(cluster_id):
            self.client.assign_networks_to_interface(
                node_id=node["id"], networks=nets, name="eth1")

        # select networks that will be untagged:
        for net in nets:
            if net["name"] in nets_to_be_checked:
                net.update(vlan_turn_off)

        # stop using VLANs:
        self.client.update_network(cluster_id,
                                   networks=nets)

        # run network check:
        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 2)

        # deploy cluster:
        task = self.deploy_cluster(cluster_id)
        self.assertTaskSuccess(task)

        #run network check again:
        task = self._run_network_verify(cluster_id)
        self.assertTaskSuccess(task, 60 * 2)



