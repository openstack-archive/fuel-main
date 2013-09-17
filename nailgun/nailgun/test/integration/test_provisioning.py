# -*- coding: utf-8 -*-

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

import mock
from mock import patch

from nailgun.test.base import BaseIntegrationTest
from nailgun.test.base import fake_tasks


class TestProvisioning(BaseIntegrationTest):

    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_nodes_in_cluster(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False, "pending_addition": True},
                {"api": False, "cluster_id": None}
            ]
        )
        cluster_db = self.env.clusters[0]
        map(cluster_db.nodes.append, self.env.nodes[:2])
        self.db.add(cluster_db)
        self.db.commit()

        self.assertEqual(len(cluster_db.nodes), 2)

    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_node_status_changes_to_provision(self, mocked_rpc=None):
        cluster = self.env.create_cluster()
        map(
            lambda x: self.env.create_node(
                api=False,
                cluster_id=cluster['id'],
                **x),
            [
                {"status": "ready"},
                {"pending_addition": True},
                {"status": "provisioning", "pending_addition": True},
                {"status": "deploying", "pending_addition": True},
                {"status": "error", "error_type": "deploy"},
                {"status": "error", "error_type": "provision"},
            ]
        )
        cluster = self.env.clusters[0]
        cluster.clear_pending_changes()

        self.env.network_manager.assign_ips = mock.MagicMock()
        self.env.launch_deployment()

        self.env.refresh_nodes()
        self.assertEquals(self.env.nodes[0].status, 'ready')
        # FIXME node status is not updated into "provisioning" for fake tasks
        self.assertEquals(self.env.nodes[1].status, 'discover')
        self.assertEquals(self.env.nodes[2].status, 'provisioning')
        self.assertEquals(self.env.nodes[3].status, 'provisioned')
        self.assertEquals(self.env.nodes[4].status, 'error')
        # FIXME node status is not updated into "provisioning" for fake tasks
        self.assertEquals(self.env.nodes[5].status, 'error')
