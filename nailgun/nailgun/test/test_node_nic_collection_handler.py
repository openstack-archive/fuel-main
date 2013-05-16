# -*- coding: utf-8 -*-
import unittest
import json

from nailgun.api.models import Node
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse


class TestHandlers(BaseHandlers):

    def test_get_handler_without_nodes(self):
        resp = self.app.get(
            reverse('NodeCollectionNICsHandler'),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        self.assertEquals(response, [])

    def test_get_handler_with_one_node_without_NICs(self):
        node = self.env.create_node(api=True)
        resp = self.app.get(
            reverse('NodeCollectionNICsHandler'),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        self.assertEquals(len(response), 1)
        resp_node = response.pop()
        self.assertEquals(resp_node['id'], node['id'])
        self.assertEquals(resp_node['interfaces'], [])

    def test_get_handler_with_two_nodes_without_NICs(self):
        nodes = []
        nodes.append(self.env.create_node(api=True))
        nodes.append(self.env.create_node(api=True))
        resp = self.app.get(
            reverse('NodeCollectionNICsHandler'),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        self.assertEquals(len(response), 2)
        resp_node1 = response.pop()
        for resp_node in response:
            node = filter(
                lambda n: n['id'] == resp_node['id'],
                nodes
            )[0]
            self.assertEquals(resp_node['id'], node['id'])
            self.assertEquals(resp_node['interfaces'], [])

