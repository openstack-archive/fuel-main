# -*- coding: utf-8 -*-
import json

from paste.fixture import TestApp

from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Node, Notification


class TestHandlers(BaseHandlers):
    def test_node_list_empty(self):
        resp = self.app.get(
            reverse('NodeCollectionHandler'),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals([], response)

    def test_notification_node_id(self):
        node = self.env.create_node(api=True)
        notif = self.db.query(Notification).first()
        self.assertEqual(node['id'], notif.node_id)
        resp = self.app.get(
            reverse('NotificationCollectionHandler'),
            headers=self.default_headers
        )
        notif_api = json.loads(resp.body)[0]
        self.assertEqual(node['id'], notif_api['node_id'])

    def test_node_get_with_cluster(self):
        self.env.create(
            cluster_kwargs={"api": False},
            nodes_kwargs=[
                {"cluster_id": None},
                {},
            ]
        )
        cluster = self.env.clusters[0]

        resp = self.app.get(
            reverse('NodeCollectionHandler'),
            params={'cluster_id': cluster.id},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(1, len(response))
        self.assertEquals(
            self.env.nodes[1].id,
            response[0]['id']
        )

    def test_node_get_with_cluster_None(self):
        self.env.create(
            cluster_kwargs={"api": False},
            nodes_kwargs=[
                {"cluster_id": None},
                {},
            ]
        )

        resp = self.app.get(
            reverse('NodeCollectionHandler'),
            params={'cluster_id': ''},
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(1, len(response))
        self.assertEquals(self.env.nodes[0].id, response[0]['id'])

    def test_node_get_without_cluster_specification(self):
        self.env.create(
            cluster_kwargs={"api": False},
            nodes_kwargs=[
                {"cluster_id": None},
                {},
            ]
        )

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
                        'meta': self.env.default_metadata()}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 201)
        node = self.db.query(Node).filter(Node.mac == 'ASDFAAASDFAA').one()
        response = json.loads(resp.body)
        self.assertEquals('discover', response['status'])

    def test_node_update(self):
        node = self.env.create_node(api=False)
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
        self.assertEquals('new', node.manufacturer)

    def test_node_create_ext_mac(self):
        node1 = self.env.create_node(
            api=False
        )
        node2_json = {
            "mac": self.env._generate_random_mac(),
            "meta": self.env.default_metadata()
        }
        node2_json["meta"]["interfaces"][0]["mac"] = node1.mac
        resp = self.app.post(
            reverse('NodeCollectionHandler'),
            json.dumps(node2_json),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 409)

    def test_node_update_ext_mac(self):
        meta = self.env.default_metadata()
        node1 = self.env.create_node(
            api=False,
            mac=meta["interfaces"][0]["mac"],
            meta={}
        )
        node1_json = {
            "mac": self.env._generate_random_mac(),
            "meta": meta
        }
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([node1_json]),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEqual(resp.status, 200)
        response = json.loads(resp.body)
        self.assertEqual(node1.mac, response[0]["mac"])
        self.assertNotEqual(node1_json["mac"], response[0]["mac"])

    def test_duplicated_node_create_fails(self):
        node = self.env.create_node(api=False)
        resp = self.app.post(
            reverse('NodeCollectionHandler'),
            json.dumps({'mac': node.mac}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(409, resp.status)
