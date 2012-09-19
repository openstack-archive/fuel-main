# -*- coding: utf-8 -*-
import json
from paste.fixture import TestApp
from base import BaseHandlers
from base import reverse


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
