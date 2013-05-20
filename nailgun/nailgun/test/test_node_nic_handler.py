# -*- coding: utf-8 -*-
import unittest
import json

from nailgun.api.models import Node
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):

    def test_get_handler_with_wrong_nodeid(self):
        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': 1}),
            expect_errors=True,
            headers=self.default_headers)
        self.assertEquals(resp.status, 404)

    def test_get_handler_with_incompleted_data(self):
        node = self.env.create_node(api=True)
        meta_list = [
            {'interfaces': None},
            {'interfaces': {}},
            {'interfaces': [{'name': '', 'mac': '00:00:00'}]},
            {'interfaces': [{'name': 'eth0', 'mac': ''}]},
            {'interfaces': [{'mac': '00:00:00'}]},
            {'interfaces': [{'name': 'eth0'}]},
            {'interfaces': [{'name': 'eth0', 'mac': '00:00:00',
                             'max_speed': -100}]},
            {'interfaces': [{'name': 'eth0', 'mac': '00:00:00',
                             'max_speed': 10.0}]},
            {'interfaces': [{'name': 'eth0', 'mac': '00:00:00',
                             'max_speed': '100'}]},
            {'interfaces': [{'name': 'eth0', 'mac': '00:00:00',
                             'current_speed': 10.0}]},
            {'interfaces': [{'name': 'eth0', 'mac': '00:00:00',
                             'current_speed': -100}]},
            {'interfaces': [{'name': 'eth0', 'mac': '00:00:00',
                             'current_speed': '100'}]},
        ]
        for meta in meta_list:
            node_data = {'mac': node['mac'], 'is_agent': True,
                         'meta': meta}
            resp = self.app.put(
                reverse('NodeCollectionHandler'),
                json.dumps([node_data]),
                expect_errors=True,
                headers=self.default_headers)
            self.assertEquals(resp.status, 400)
            resp = self.app.get(
                reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
                headers=self.default_headers)
            self.assertEquals(resp.status, 200)
            response = json.loads(resp.body)
            self.assertEquals(response, [])

    def test_get_handler_without_NICs(self):
        node = self.env.create_node(api=True)
        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        self.assertEquals(response, [])

    def test_get_handler_with_NICs(self):
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': '123', 'current_speed': 1, 'max_speed': 1},
            {'name': 'eth1', 'mac': '678', 'current_speed': 1, 'max_speed': 1},
        ]}
        node = self.env.create_node(api=True, meta=meta)
        node_db = self.env.nodes[0]
        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node_db.id}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        self.assertItemsEqual(
            map(lambda i: i['id'], response),
            map(lambda i: i.id, node_db.interfaces)
        )
        for nic in meta['interfaces']:
            filtered_nics = filter(
                lambda i: i['mac'] == nic['mac'],
                response
            )
            resp_nic = filtered_nics[0]
            self.assertEquals(resp_nic['mac'], nic['mac'])
            self.assertEquals(resp_nic['current_speed'], nic['current_speed'])
            self.assertEquals(resp_nic['max_speed'], nic['max_speed'])
            for conn in ('assigned_networks', 'allowed_networks'):
                self.assertEquals(resp_nic[conn], [])

    def test_NIC_removes_by_agent(self):
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': '12345', 'current_speed': 1},
        ]}
        node = self.env.create_node(api=True, meta=meta)

        node_data = {'mac': node['mac'], 'is_agent': True,
                     'meta': {'interfaces': []}}
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([node_data]),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        self.assertEquals(response, [])

    def test_NIC_updates_by_agent(self):
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': '12345', 'current_speed': 1},
        ]}
        node = self.env.create_node(api=True, meta=meta)
        new_meta = {'interfaces': [
            {'name': 'new_nic', 'mac': '12345', 'current_speed': 10,
             'max_speed': 10},
        ]}
        node_data = {'mac': node['mac'], 'is_agent': True,
                     'meta': new_meta}
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([node_data]),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        self.assertEquals(len(response), 1)
        resp_nic = response[0]
        nic = new_meta['interfaces'][0]
        self.assertEquals(resp_nic['mac'], nic['mac'])
        self.assertEquals(resp_nic['current_speed'], nic['current_speed'])
        self.assertEquals(resp_nic['max_speed'], nic['max_speed'])
        for conn in ('assigned_networks', 'allowed_networks'):
            self.assertEquals(resp_nic[conn], [])

    def test_NIC_adds_by_agent(self):
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': '12345', 'current_speed': 1},
        ]}
        node = self.env.create_node(api=True, meta=meta)

        meta['interfaces'].append({'name': 'new_nic', 'mac': '643'})
        node_data = {'mac': node['mac'], 'is_agent': True,
                     'meta': meta}
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([node_data]),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        self.assertEquals(len(response), len(meta['interfaces']))
        for nic in meta['interfaces']:
            filtered_nics = filter(
                lambda i: i['mac'] == nic['mac'],
                response
            )
            resp_nic = filtered_nics[0]
            self.assertEquals(resp_nic['mac'], nic['mac'])
            self.assertEquals(resp_nic['current_speed'],
                              nic.get('current_speed'))
            self.assertEquals(resp_nic['max_speed'], nic.get('max_speed'))
            for conn in ('assigned_networks', 'allowed_networks'):
                self.assertEquals(resp_nic[conn], [])

    def test_ignore_NIC_id_in_meta(self):
        fake_id = 'some_data'
        meta = {'interfaces': [
            {'id': fake_id, 'name': 'eth0', 'mac': '12345'},
        ]}
        node = self.env.create_node(api=True, meta=meta)
        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        self.assertNotEquals(response[0]['id'], fake_id)

