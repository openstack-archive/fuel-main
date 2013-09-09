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

import json

from nailgun.api.models import Node
from nailgun.test.base import BaseIntegrationTest
from nailgun.test.base import reverse


class TestHandlers(BaseIntegrationTest):

    def test_node_get(self):
        node = self.env.create_node(api=False)
        resp = self.app.get(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            headers=self.default_headers)
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(node.id, response['id'])
#       todo: decide None output format
#        self.assertEquals(node.name, response['name'])
        self.assertEquals(node.mac, response['mac'])
        self.assertEquals(
            node.pending_addition, response['pending_addition'])
        self.assertEquals(
            node.pending_deletion, response['pending_deletion'])
        self.assertEquals(node.status, response['status'])
        self.assertEquals(
            node.meta['cpu']['total'],
            response['meta']['cpu']['total']
        )
        self.assertEquals(node.meta['disks'], response['meta']['disks'])
        self.assertEquals(node.meta['memory'], response['meta']['memory'])

    def test_node_creation_with_id(self):
        node_id = '080000000003'
        resp = self.app.post(
            reverse('NodeCollectionHandler'),
            json.dumps({'id': node_id,
                        'mac': 'ASDFAAASDFAA',
                        'status': 'discover'}),
            headers=self.default_headers,
            expect_errors=True)
        # we now just ignore 'id' if present
        self.assertEquals(201, resp.status)

    def test_node_deletion(self):
        node = self.env.create_node(api=False)
        resp = self.app.delete(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            "",
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 204)

    def test_node_valid_metadata_gets_updated(self):
        new_metadata = self.env.default_metadata()
        node = self.env.create_node(api=False)
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'meta': new_metadata}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        self.db.refresh(node)

        nodes = self.db.query(Node).filter(
            Node.id == node.id
        ).all()
        self.assertEquals(len(nodes), 1)
        self.assertEquals(nodes[0].meta, new_metadata)

    def test_node_valid_status_gets_updated(self):
        node = self.env.create_node(api=False)
        params = {'status': 'error'}
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps(params),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)

    def test_node_action_flags_are_set(self):
        flags = ['pending_addition', 'pending_deletion']
        node = self.env.create_node(api=False)
        for flag in flags:
            resp = self.app.put(
                reverse('NodeHandler', kwargs={'node_id': node.id}),
                json.dumps({flag: True}),
                headers=self.default_headers
            )
            self.assertEquals(resp.status, 200)
            self.db.refresh(node)

        node_from_db = self.db.query(Node).filter(
            Node.id == node.id
        ).first()
        for flag in flags:
            self.assertEquals(getattr(node_from_db, flag), True)

    def test_put_returns_400_if_no_body(self):
        node = self.env.create_node(api=False)
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            "",
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

    def test_put_returns_400_if_wrong_status(self):
        node = self.env.create_node(api=False)
        params = {'status': 'invalid_status'}
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps(params),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)
