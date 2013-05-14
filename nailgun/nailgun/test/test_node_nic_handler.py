# -*- coding: utf-8 -*-
import unittest
import json

from nailgun.api.models import Node
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):

    def test_NICs_get(self):
        # should be created with more than 1 interface
        meta = self.env.default_metadata()
        node = self.env.create_node(api=True, meta=meta)
        node_db = self.env.nodes[0]
        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node_db.id}),
            headers=self.default_headers)
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(node_db.id, response['id'])
        self.assertItemsEqual(
            map(lambda i: i.id, node_db.interfaces),
            map(lambda i: i['id'], response['interfaces'])
        )
        for nic in meta['interfaces']:
            filtered_nics = filter(
                lambda i: i['mac'] == nic['mac'],
                response['interfaces']
            )
            resp_nic = filtered_nics[0]
            self.assertEquals(nic['mac'], resp_nic['mac'])
            self.assertEquals(nic['current_speed'], resp_nic['current_speed'])
            self.assertEquals(nic['max_speed'], resp_nic['max_speed'])
            for conn in ('assigned_networks', 'allowed_networks'):
                self.assertEquals(resp_nic[conn], [])
