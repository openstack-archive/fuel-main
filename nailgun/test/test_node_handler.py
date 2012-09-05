# -*- coding: utf-8 -*-
import unittest
import json
from paste.fixture import TestApp
from api.models import Node
from base import BaseHandlers
from base import reverse


class TestHandlers(BaseHandlers):

    def test_node_get(self):
        node = self.create_default_node()
        resp = self.app.get(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            headers=self.default_headers)
        self.assertEquals(200, resp.status)
        response = json.loads(resp.body)
        self.assertEquals(node.id, response['id'])
#       todo: decide None output format
#        self.assertEquals(node.name, response['name'])
        self.assertEquals(node.mac, response['mac'])
        self.assertEquals(node.redeployment_needed, response['redeployment_needed'])
        self.assertEquals(node.status, response['status'])
        self.assertEquals(node.roles, response['roles'])
        self.assertEquals(node.new_roles, response['new_roles'])
        self.assertEquals(node.info['cores'], response['info']['cores'])
        self.assertEquals(node.info['hdd'], response['info']['hdd'])
        self.assertEquals(node.info['ram'], response['info']['ram'])
        self.assertEquals(node.info['cpu'], response['info']['cpu'])


    def test_node_creation_with_id(self):
        node_id = '080000000003'
        resp = self.app.post(
            reverse('NodeCollectionHandler'),
            json.dumps({'id': node_id, 'mac': 'ASDFAAASDFAA'}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(400, resp.status)

    def test_node_creation(self):
        resp = self.app.post(
            reverse('NodeCollectionHandler'),
            json.dumps({'mac': 'ASDFAAASDFAA'}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 201)
        node = self.db.query(Node).filter(Node.mac == 'ASDFAAASDFAA').one()
        response = json.loads(resp.body)
        self.assertEquals('ready', response['status'])

    def test_node_deletion(self):
        node = self.create_default_node()
        resp = self.app.delete(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            "",
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 204)

    @unittest.skip('wth?')
    def test_node_creation_using_put(self):
        node_id = '080000000002'

        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node_id}),
            json.dumps({}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)

        nodes_from_db = self.db.query(Node).filter(id=node_id)
        self.assertEquals(len(nodes_from_db), 1)

    def test_node_valid_metadata_gets_updated(self):
        new_metadata = self.default_metadata()
        node = self.create_default_node()
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
        node = self.create_default_node()
        params = {'status': 'error'}
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps(params),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)

    def test_node_valid_list_of_new_roles_gets_updated(self):
        node = self.create_default_node()
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({
                'redeployment_needed': True
            }),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)
        self.db.refresh(node)

        node_from_db = self.db.query(Node).filter(
            Node.id == node.id
        ).first()
        self.assertEquals(node_from_db.redeployment_needed, True)

    def test_put_returns_400_if_no_body(self):
        node = self.create_default_node()
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            "",
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

    def test_put_returns_415_if_wrong_content_type(self):
        node = self.create_default_node()
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'meta': json.dumps(self.default_metadata())}),
            headers={"Content-Type": "plain/text"},
            expect_errors=True
        )
        self.assertEquals(resp.status, 415)

    def test_put_returns_400_if_wrong_status(self):
        node = self.create_default_node()
        params = {'status': 'invalid_status'}
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps(params),
            headers=self.default_headers,
            expect_errors=True)
        print resp
        self.assertEquals(resp.status, 400)

    @unittest.skip('no validation of metadata')
    def test_put_returns_400_if_no_block_device_attr(self):
        node = self.create_default_node()
        old_meta = self.create_default_node().metadata
        new_meta = self.default_metadata()
        del new_meta['block_device']
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'metadata': new_meta}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

        node_from_db = Node.objects.get(id=self.create_default_node().id)
        self.assertEquals(node_from_db.metadata, old_meta)

    @unittest.skip('no validation of metadata')
    def test_put_returns_400_if_no_interfaces_attr(self):
        node = self.create_default_node()
        old_meta = self.create_default_node().metadata
        new_meta = self.default_metadata()
        del new_meta['interfaces']
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'metadata': new_meta}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

        node_from_db = Node.objects.get(id=self.create_default_node().id)
        self.assertEquals(node_from_db.metadata, old_meta)

    @unittest.skip('no validation of metadata')
    def test_put_returns_400_if_interfaces_empty(self):
        node = self.create_default_node()
        old_meta = node.metadata
        new_meta = {'asdf': ['fdsa', 'asdf'], 'interfaces': ""}
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'metadata': new_meta}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

        node_from_db = Node.objects.get(id=node.id)
        self.assertEquals(node_from_db.metadata, old_meta)

    @unittest.skip('no validation of metadata')
    def test_put_returns_400_if_no_cpu_attr(self):
        node = self.create_default_node()
        old_meta = self.create_default_node().metadata
        new_meta = self.default_metadata()
        del new_meta['cpu']
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'metadata': new_meta}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

        node_from_db = Node.objects.get(id=self.create_default_node().id)
        self.assertEquals(node_from_db.metadata, old_meta)

    @unittest.skip('no validation of metadata')
    def test_put_returns_400_if_no_memory_attr(self):
        node = self.create_default_node()
        old_meta = self.create_default_node().metadata
        new_meta = self.default_metadata()
        del new_meta['memory']
        resp = self.app.put(
            reverse('NodeHandler', kwargs={'node_id': node.id}),
            json.dumps({'metadata': new_meta}),
            headers=self.default_headers,
            expect_errors=True)
        self.assertEquals(resp.status, 400)

        node_from_db = Node.objects.get(id=self.create_default_node().id)
        self.assertEquals(node_from_db.metadata, old_meta)
