# -*- coding: utf-8 -*-

import json
import logging
import unittest
from mock import patch

from nailgun.settings import settings
from nailgun.logger import logger
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster
from nailgun.test.base import fake_tasks


class TestProvisioning(BaseHandlers):

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

        self.env.network_manager.assign_ips = self.mock.MagicMock()

        self.env.launch_deployment()

    @fake_tasks(fake_rpc=False, mock_rpc=False)
    @patch('nailgun.rpc.cast')
    def test_node_status_changes_to_provision(self, mocked_rpc=None):
        cluster = self.env.create_cluster()
        map(
            lambda x: self.env.create_node(
                api=True,
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

        self.env.network_manager.assign_ips = self.mock.MagicMock()
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
