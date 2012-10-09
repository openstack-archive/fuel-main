# -*- coding: utf-8 -*-

import json
import logging
import unittest

from settings import settings
from base import BaseHandlers
from base import reverse
from network import manager as netmanager
from mock import patch


class TestProvisioning(BaseHandlers):

    def test_nodes_in_cluster(self):
        cluster = self.create_default_cluster()
        node = self.create_default_node()
        node2 = self.create_default_node()
        node2.status = "discover"
        node3 = self.create_default_node()
        cluster.nodes.append(node)
        cluster.nodes.append(node2)
        self.db.add(cluster)
        self.db.commit()

        self.assertEqual(len(cluster.nodes), 2)

        netmanager.assign_ips = self.mock.MagicMock()

        with patch('api.handlers.cluster.Cobbler'):
            resp = self.app.put(
                reverse(
                    'ClusterChangesHandler',
                    kwargs={"cluster_id": cluster.id}),
                "",
                headers=self.default_headers
            )
            self.assertEquals(200, resp.status)
