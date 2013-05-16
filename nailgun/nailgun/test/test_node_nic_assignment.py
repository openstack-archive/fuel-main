# -*- coding: utf-8 -*-
import unittest
import json

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):

    def test_assigned_networks_when_node_added(self):
        mac = '123'
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': mac},
        ]}
        node = self.env.create_node(api=True, meta=meta, mac=mac)
        cluster = self.env.create_cluster(api=True)
        resp = self.app.put(
            reverse('ClusterHandler', kwargs={'cluster_id': cluster['id']}),
            json.dumps({'nodes': [node['id']]}),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        print response
        self.assertGreater(
            len(response['interfaces'][0]['assigned_networks']),
            0
        )

