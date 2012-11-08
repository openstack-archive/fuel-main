# -*- coding: utf-8 -*-

import json
import logging
import unittest
from mock import patch

from nailgun.settings import settings
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.network import manager as netmanager
from nailgun.api.models import Cluster


class TestProvisioning(BaseHandlers):

    def test_nodes_in_cluster(self):
        cluster = self.create_cluster_api()
        node = self.create_default_node()
        node2 = self.create_default_node()
        node2.status = "discover"
        node3 = self.create_default_node()
        cluster_db = self.db.query(Cluster).get(cluster['id'])
        cluster_db.nodes.append(node)
        cluster_db.nodes.append(node2)
        self.db.add(cluster_db)
        self.db.commit()

        self.assertEqual(len(cluster_db.nodes), 2)

        netmanager.assign_ips = self.mock.MagicMock()

        with patch('nailgun.task.task.Cobbler'):
            resp = self.app.put(
                reverse(
                    'ClusterChangesHandler',
                    kwargs={"cluster_id": cluster['id']}),
                "",
                headers=self.default_headers
            )
            self.assertEquals(200, resp.status)
