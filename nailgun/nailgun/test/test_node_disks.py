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

import unittest
import json
from paste.fixture import TestApp

from nailgun.api.models import Node, Notification
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):

    def test_attrs_creation(self):
        node = self.env.create_node(
            api=True
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
        node = self.env.create_node(api=True)
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
        node = self.env.create_node(api=True)
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
        node = self.env.create_node(api=True)
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
        node = self.env.create_node(api=True)
        node_db = self.env.nodes[0]
        test_data = {"volumes": []}
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
        node = self.env.create_node(api=True)
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
        cluster = self.env.create_cluster(api=False)
        node = self.env.create_node(
            api=True,
            role="compute",  # vgs: os, vm
            cluster_id=cluster.id
        )
        node_db = self.env.nodes[0]
        resp = self.app.get(
            reverse(
                'NodeAttributesByNameHandler',
                kwargs={
                    'node_id': node_db.id,
                    'attr_name': 'volumes'
                }
            ) + "?type=disk",
            headers=self.default_headers
        )
        response = json.loads(resp.body)
        self.assertEquals(len(response), 6)

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
                'NodeAttributesByNameHandler',
                kwargs={
                    'node_id': node_db.id,
                    'attr_name': 'volumes'
                }
            ) + "?type=disk",
            headers=self.default_headers
        )
        response = json.loads(resp.body)
        self.assertEquals(len(response), 7)

        # check all groups on all disks
        vgs = ["os", "vm"]
        for disk in response:
            check_vgs = filter(
                lambda v: v.get("vg") in vgs,
                disk['volumes']
            )
            self.assertEquals(len(check_vgs), len(vgs))

    def test_node_os_many_disks(self):
        meta = self.env.default_metadata()
        meta["memory"]["total"] = 4294967296
        meta["disks"] = [
            {
                "size": 7483648000,
                "model": "HITACHI LOL404",
                "name": "sda8",
                "disk": "blablabla2"
            },
            {
                "model": "SEAGATE B00B135",
                "name": "vda",
                "size": 2147483648000,
                "disk": "blablabla3"
            }
        ]
        node = self.env.create_node(
            api=True,
            meta=meta
        )
        node_db = self.env.nodes[0]
        volumes = node_db.attributes.volumes
        os_pv_sum = 0
        os_lv_sum = 0
        for disk in filter(lambda v: v["type"] == "disk", volumes):
            os_pv_sum += filter(
                lambda v: "vg" in v and v["vg"] == "os",
                disk["volumes"]
            )[0]["size"]
            os_pv_sum -= node_db.volume_manager.field_generator(
                "calc_lvm_meta_size"
            )
        os_vg = filter(lambda v: v["id"] == "os", volumes)[0]
        os_lv_sum += sum([v["size"] for v in os_vg["volumes"]])
        self.assertEquals(os_pv_sum, os_lv_sum)

    def test_attrs_get_by_name(self):
        node = self.env.create_node(api=True)
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
        node = self.env.create_node(api=True)
        node_db = self.env.nodes[0]
        resp = self.app.get(
            reverse('NodeAttributesByNameHandler',
                    kwargs={'node_id': node_db.id,
                            'attr_name': 'volumes'}) + "?type=vg",
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(len(response), 1)
        self.assertEquals(
            len(filter(lambda v: (v["type"] == "vg"), response)),
            1
        )

    def test_attrs_update_by_name(self):
        node = self.env.create_node(api=True)
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
        node = self.env.create_node(api=True)
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
