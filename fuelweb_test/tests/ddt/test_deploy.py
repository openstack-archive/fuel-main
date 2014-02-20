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

import logging
from proboscis import test, factory
from fuelweb_test.helpers.decorators import log_snapshot_on_error
from fuelweb_test.tests.base_test_case import TestBasic, SetupEnvironment
from fuelweb_test.tests.ddt.gtestdata import TestParamsList


#logging.basicConfig(
#    format=':%(lineno)d: %(asctime)s %(message)s',
#    level=logging.DEBUG
#)

logger = logging.getLogger(__name__)


@factory
def test_deploy_factory():
    return [TestDeploy(test_params) for test_params in TestParamsList()]


@test(groups=['ddt'])
class TestDeploy(TestBasic):

    def __init__(self, params):
        super(TestDeploy, self).__init__()
        self.params = params

    @test(depends_on=[SetupEnvironment.prepare_release])
    @log_snapshot_on_error
    def deploy_environment(self):
        logger.info(self.params)

        self.env.revert_snapshot("ready")
        self.env.bootstrap_nodes(
            self.env.devops_nodes_by_names(self.params.nodes.keys()))

        # Create environment
        cluster_id = self.fuel_web.create_cluster(
            name=self.params.name,
            release_name=self.params.release,
            mode=self.params.mode,
            settings=self.params.settings
        )
        cluster = self.fuel_web.client.get_cluster(cluster_id)

        # Add nodes to the cluster
        nailgun_nodes = \
            self.fuel_web.update_nodes(cluster_id, self.params.nodes)

        # Update node's interfaces
        for node in nailgun_nodes:
            self.fuel_web.update_node_networks(
                node['id'], self.params.interfaces)

        # Update nova parameters
        if 'net_manager' in self.params.settings:
            networks = self.fuel_web.client.get_networks(cluster_id)
            networks['net_manager'] = \
                self.params.settings['net_manager']
            self.fuel_web.client.client.put(
                "/api/clusters/%d/network_configuration/%s" %
                (cluster_id, cluster['net_provider']), networks
            )

        # Deploy changes
        self.fuel_web.deploy_cluster_wait(cluster_id)

        self.env.make_snapshot(self.params.name)
