# -*- coding: utf-8 -*-
import json

from paste.fixture import TestApp

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Node


class TestHandlers(BaseHandlers):
    def test_node_list_empty(self):
        resp = self.app.get(
            reverse('NodeCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals([], response)

    def test_node_list_big(self):
        for i in range(100):
            self.create_default_node()
        resp = self.app.get(
            reverse('NodeCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(100, len(response))

    def test_node_get_with_cluster(self):
        cluster = self.create_default_cluster()
        node1 = self.create_default_node()
        node2 = self.create_default_node(cluster_id=cluster.id)

        resp = self.app.get(
            reverse('NodeCollectionHandler'),
            params={'cluster_id': cluster.id},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(1, len(response))
        self.assertEquals(node2.id, response[0]['id'])

    def test_node_get_with_cluster_None(self):
        cluster = self.create_default_cluster()
        node1 = self.create_default_node()
        node2 = self.create_default_node(cluster_id=cluster.id)

        resp = self.app.get(
            reverse('NodeCollectionHandler'),
            params={'cluster_id': ''},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(1, len(response))
        self.assertEquals(node1.id, response[0]['id'])

    def test_node_get_without_cluster_specification(self):
        cluster = self.create_default_cluster()
        node1 = self.create_default_node()
        node2 = self.create_default_node(cluster_id=cluster.id)

        resp = self.app.get(
            reverse('NodeCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(2, len(response))

    def test_node_creation(self):
        resp = self.app.post(
            reverse('NodeCollectionHandler'),
            json.dumps({'mac': 'ASDFAAASDFAA',
                        'meta': self.default_metadata()}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 201)
        node = self.db.query(Node).filter(Node.mac == 'ASDFAAASDFAA').one()
        response = json.loads(resp.body)
        self.assertEquals('discover', response['status'])

    def test_node_update(self):
        node = self.create_default_node()
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{'mac': node.mac, 'manufacturer': 'new'}]),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        resp = self.app.get(
            reverse('NodeCollectionHandler'),
            headers=self.default_headers
        )
        self.db.refresh(node)
        node_db = self.db.query(Node).filter_by(id=node.id).first()
        self.assertEquals('new', node_db.manufacturer)

    def test_duplicated_node_create_fails(self):
        node = self.create_default_node()
        resp = self.app.post(
            reverse('NodeCollectionHandler'),
            json.dumps({'mac': node.mac}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(409, resp.status)
