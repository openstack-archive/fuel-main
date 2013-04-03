# -*- coding: utf-8 -*-
import unittest
import json
from paste.fixture import TestApp

from nailgun.api.models import Node
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):

    def test_attrs_creation(self):
        node = self.env.create_node(
            api=True,
            meta=self.env.default_metadata()
        )
        node_db = self.env.nodes[0]
        resp = self.app.get(
            reverse('NodeAttributesHandler', kwargs={'node_id': node_db.id}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(node_db.id, response["node_id"])
        self.assertEquals(
            len(filter(lambda a: ({"type": "mbr"} in a["volumes"]),
                       response["volumes"])),
            1
        )

    def test_attrs_updating(self):
        node = self.env.create_node(
            api=True,
            meta=self.env.default_metadata()
        )
        node_db = self.env.nodes[0]
        test_data = {"volumes": "test"}
        resp = self.app.put(
            reverse('NodeAttributesHandler', kwargs={'node_id': node_db.id}),
            json.dumps(test_data),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        test_data.update({"node_id": node_db.id})
        self.assertEquals(response, test_data)

    def test_attrs_get_by_name(self):
        node = self.env.create_node(
            api=True,
            meta=self.env.default_metadata()
        )
        node_db = self.env.nodes[0]
        resp = self.app.get(
            reverse('NodeAttributesByNameHandler',
                    kwargs={'node_id': node_db.id,
                            'attr_name': 'volumes'}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(
            len(filter(lambda a: ({"type": "mbr"} in a["volumes"]),
                       response)),
            1
        )

    def test_attrs_get_by_name_type(self):
        node = self.env.create_node(
            api=True,
            meta=self.env.default_metadata()
        )
        node_db = self.env.nodes[0]
        resp = self.app.get(
            reverse('NodeAttributesByNameHandler',
                    kwargs={'node_id': node_db.id,
                            'attr_name': 'volumes'}) + "?type=vg",
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(len(response), 2)
        self.assertEquals(
            len(filter(lambda v: (v["type"] == "vg"), response)),
            2
        )

    def test_attrs_update_by_name(self):
        node = self.env.create_node(
            api=True,
            meta=self.env.default_metadata()
        )
        node_db = self.env.nodes[0]
        test_data = [
            {
                "id": "test",
                "volumes": "test"
            }
        ]
        resp = self.app.put(
            reverse('NodeAttributesByNameHandler',
                    kwargs={'node_id': node_db.id,
                            'attr_name': 'volumes'}),
            json.dumps(test_data),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(len(response), 1)
        self.assertEquals(
            response,
            test_data
        )
