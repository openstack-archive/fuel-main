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

    def test_attrs_creation_put(self):
        node = self.env.create_node(
            api=True,
            meta=self.env.default_metadata()
        )
        node_db = self.env.nodes[0]
        resp = self.app.put(
            reverse('NodeAttributesHandler', kwargs={'node_id': node_db.id}),
            json.dumps({"volumes": []}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(response["volumes"], [])
        resp = self.app.get(
            reverse('NodeAttributesHandler', kwargs={'node_id': node_db.id}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(response["volumes"], [])
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{"mac": node_db.mac, "is_agent": True}]),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        resp = self.app.get(
            reverse('NodeAttributesHandler', kwargs={'node_id': node_db.id}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertNotEquals(response["volumes"], [])

    def test_get_default_attrs(self):
        node = self.env.create_node(
            api=True,
            meta=self.env.default_metadata()
        )
        node_db = self.env.nodes[0]
        resp = self.app.get(
            reverse('NodeAttributesDefaultsHandler',
                    kwargs={'node_id': node_db.id}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(
            response['volumes'],
            node_db.volume_manager.gen_default_volumes_info()
        )

    def test_get_default_attrs_volumes(self):
        node = self.env.create_node(
            api=True,
            meta=self.env.default_metadata()
        )
        node_db = self.env.nodes[0]
        resp = self.app.get(
            reverse('NodeAttributesByNameDefaultsHandler',
                    kwargs={
                        'node_id': node_db.id,
                        'attr_name': 'volumes'
                    }),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(
            response,
            node_db.volume_manager.gen_default_volumes_info()
        )

    def test_reset_attrs_to_default(self):
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
        response = json.loads(resp.body)
        self.assertNotEquals(
            response['volumes'],
            node_db.volume_manager.gen_default_volumes_info()
        )
        resp = self.app.put(
            reverse('NodeAttributesDefaultsHandler',
                    kwargs={'node_id': node_db.id}),
            json.dumps({}),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(
            response['volumes'],
            node_db.volume_manager.gen_default_volumes_info()
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

    def test_node_disk_amount_regenerates_volumes_info(self):
        node = self.env.create_node(
            api=True,
            meta=self.env.default_metadata()
        )
        node_db = self.env.nodes[0]
        resp = self.app.get(
            reverse(
                'NodeAttributesHandler',
                kwargs={
                    'node_id': node_db.id,
                    'attr_name': 'volumes'
                }
            ),
            headers=self.default_headers
        )
        response = json.loads(resp.body)
        self.assertEquals(len(response["volumes"]), 3)
        new_meta = node_db.meta.copy()
        new_meta["disks"].append({
            "size": 1000022933376,
            "model": "SAMSUNG B00B135",
            "name": "sda",
            "disk": "disk/id/b00b135"
        })
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([
                {
                    "mac": node_db.mac,
                    "meta": new_meta,
                    "is_agent": True
                }
            ]),
            headers=self.default_headers
        )
        self.env.refresh_nodes()
        resp = self.app.get(
            reverse(
                'NodeAttributesHandler',
                kwargs={
                    'node_id': node_db.id,
                    'attr_name': 'volumes'
                }
            ),
            headers=self.default_headers
        )
        response = json.loads(resp.body)
        self.assertEquals(len(response["volumes"]), 4)

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

    def test_attrs_update_by_name_type(self):
        node = self.env.create_node(
            api=True,
            meta=self.env.default_metadata()
        )
        node_db = self.env.nodes[0]
        test_data1 = [
            {
                "id": "test",
                "type": "disk",
                "volumes": [
                    {"test": "ololo"}
                ]
            },
            {
                "id": "test2",
                "type": "vg",
                "volumes": [
                    {"test": "ololo2"}
                ]
            }
        ]
        resp = self.app.put(
            reverse('NodeAttributesByNameHandler',
                    kwargs={'node_id': node_db.id,
                            'attr_name': 'volumes'}),
            json.dumps(test_data1),
            headers=self.default_headers
        )
        test_data2 = [{
            "id": "test",
            "type": "disk",
            "volumes": [
                {"test": "derp"}
            ]
        }]
        resp = self.app.put(
            reverse('NodeAttributesByNameHandler',
                    kwargs={'node_id': node_db.id,
                            'attr_name': 'volumes'}) + "?type=disk",
            json.dumps(test_data2),
            headers=self.default_headers
        )
        response = json.loads(resp.body)
        self.assertEquals(response, test_data2)
        self.assertEquals(len(response), 1)
        self.env.refresh_nodes()
        self.assertEquals(len(node_db.attributes.volumes), 2)
        self.assertEquals(
            len(
                filter(lambda t: t["type"] == "disk",
                       node_db.attributes.volumes)
            ),
            1
        )
        self.assertEquals(
            filter(
                lambda t: t["type"] == "disk",
                node_db.attributes.volumes
            )[0]["volumes"][0]["test"],
            "derp"
        )
