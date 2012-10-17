# -*- coding: utf-8 -*-

import json
import logging
import unittest
from mock import patch

from nailgun.settings import settings
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.network import manager as netmanager


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

        with patch('nailgun.api.handlers.cluster.Cobbler'):
            resp = self.app.put(
                reverse(
                    'ClusterChangesHandler',
                    kwargs={"cluster_id": cluster.id}),
                "",
                headers=self.default_headers
            )
            self.assertEquals(200, resp.status)
