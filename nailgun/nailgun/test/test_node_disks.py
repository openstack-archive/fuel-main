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
from nailgun.db import db


class TestNodeDisksHandlers(BaseHandlers):

    def get(self, node_id):
        resp = self.app.get(
            reverse('NodeDisksHandler', kwargs={'node_id': node_id}),
            headers=self.default_headers)

        self.assertEquals(200, resp.status)
        return json.loads(resp.body)

    def put(self, node_id, data):
        resp = self.app.put(
            reverse('NodeDisksHandler', kwargs={'node_id': node_id}),
            json.dumps(data),
            headers=self.default_headers)

        self.assertEquals(200, resp.status)
        return json.loads(resp.body)

    def test_default_attrs_after_creation(self):
        node = self.env.create_node(api=True)
        node_db = self.env.nodes[0]
        disks = self.get(node_db.id)

        self.assertGreater(len(disks), 0)
        for disk in disks:
            self.assertTrue(type(disk['size']) in (float, int))
            self.assertGreaterEqual(disk['size'], 0)
            self.assertGreater(len(disk['volumes']), 0)

    def test_disks_recreation_after_node_agent_request(self):
        node = self.env.create_node(api=True)
        node_db = self.env.nodes[0]
        response = self.put(node_db.id, [])
        self.assertEquals(response, [])

        response = self.get(node_db.id)
        self.assertEquals(response, [])

        # FIXME: check, should we regenerate all info about disks
        # if some disk removed/updated/changed ?
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{"mac": node_db.mac, "is_agent": True}]),
            headers=self.default_headers)
        self.assertEquals(200, resp.status)

        response = self.get(node_db.id)
        self.assertNotEquals(response, [])

    def test_node_os_many_disks(self):
        meta = self.env.default_metadata()
        meta['memory']['total'] = 4294967296
        meta['disks'] = [
            {
                'size': 7483648000,
                'model': 'HITACHI LOL404',
                'name': 'sda8',
                'disk': 'blablabla2'
            },
            {
                'model': 'SEAGATE B00B135',
                'name': 'vda',
                'size': 2147483648000,
                'disk': 'blablabla3'
            }
        ]
        node = self.env.create_node(
            api=True,
            meta=meta)

        node_db = self.env.nodes[0]
        volumes = node_db.attributes.volumes
        os_pv_sum = 0
        os_lv_sum = 0

        for disk in filter(lambda v: v['type'] == 'disk', volumes):
            os_pv_sum += filter(
                lambda v: 'vg' in v and v['vg'] == 'os',
                disk['volumes']
            )[0]['size']
            os_pv_sum -= node_db.volume_manager.call_generator(
                'calc_lvm_meta_size')

        os_vg = filter(lambda v: v['id'] == 'os', volumes)[0]
        os_lv_sum += sum([v['size'] for v in os_vg['volumes']])
        self.assertEquals(os_pv_sum, os_lv_sum)


class TestNodeDefaultsDisksHandler(BaseHandlers):

    def get(self, node_id):
        resp = self.app.get(
            reverse('NodeDefaultsDisksHandler', kwargs={'node_id': node_id}),
            headers=self.default_headers)

        self.assertEquals(200, resp.status)
        return json.loads(resp.body)

    def test_node_disk_amount_regenerates_volumes_info_if_new_disk_added(self):
        cluster = self.env.create_cluster(api=False)
        node = self.env.create_node(
            api=True,
            role='compute',  # vgs: os, vm
            cluster_id=cluster.id)
        node_db = self.env.nodes[0]
        response = self.get(node_db.id)
        self.assertEquals(len(response), 6)

        new_meta = node_db.meta.copy()
        new_meta['disks'].append({
            'size': 1000022933376,
            'model': 'SAMSUNG B00B135',
            'name': 'sda',
            'disk': 'disk/id/b00b135'})

        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{
                "mac": node_db.mac,
                "meta": new_meta,
                "is_agent": True}]),
            headers=self.default_headers)

        self.env.refresh_nodes()

        response = self.get(node_db.id)
        self.assertEquals(len(response), 7)

        # check all groups on all disks
        vgs = ["os", "vm"]
        for disk in response:
            check_vgs = filter(
                lambda v: v.get("vg") in vgs,
                disk['volumes'])
            self.assertEquals(len(check_vgs), len(vgs))

    def test_get_default_attrs(self):
        node = self.env.create_node(api=True)
        node_db = self.env.nodes[0]
        resp = self.get(node_db.id)

        default_volumes = node_db.volume_manager.gen_default_volumes_info()
        self.assertItemsEqual(
            resp,
            filter(lambda volume: volume['type'] == 'disk', default_volumes))


class TestNodeVolumesInformationHandler(BaseHandlers):

    def get(self, node_id):
        resp = self.app.get(
            reverse('NodeVolumesInformationHandler', kwargs={'node_id': node_id}),
            headers=self.default_headers)

        self.assertEquals(200, resp.status)
        return json.loads(resp.body)

    def create_node(self, role):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[{'role': role, 'pending_addition': True}])

        return self.env.nodes[0]

    def check_volumes(self, volumes, volumes_ids):
        self.assertEquals(len(volumes), len(volumes_ids))
        for volume_id in volumes_ids:
            # Volume has name
            volume = filter(
                lambda volume: volume['name'] == volume_id, volumes)[0]
            # min_size
            self.assertTrue(type(volume['min_size']) in (float, int))
            self.assertGreaterEqual(volume['min_size'], 0)
            # and label
            self.assertTrue(type(volume['label']) in (str, unicode))
            self.assertGreater(volume['label'], 0)

    def test_volumes_information_for_cinder_role(self):
        node_db = self.create_node('cinder')
        response = self.get(node_db.id)
        self.check_volumes(response, ['os', 'cinder'])

    def test_volumes_information_for_compute_role(self):
        node_db = self.create_node('compute')
        response = self.get(node_db.id)
        self.check_volumes(response, ['os', 'vm'])

    def test_volumes_information_for_controller_role(self):
        node_db = self.create_node('controller')
        response = self.get(node_db.id)
        self.check_volumes(response, ['os'])
