import simplejson as json
from django import http
from django.test import TestCase

from nailgun.models import Node


class TestHandlers(TestCase):

    def setUp(self):
        self.request = http.HttpRequest()
        self.old_meta = {'block_device': 'value',
                         'interfaces': 'val2',
                         'cpu': 'asf',
                         'memory': 'sd'
                        }
        self.node_name = "test.server.com"

        self.node = Node(environment_id=1,
                    name=self.node_name,
                    metadata=self.old_meta)
        self.node.save()
        self.node_url = '/api/environments/1/nodes/' + self.node_name

        self.new_meta = {'block_device': 'new-val',
                         'interfaces': 'd',
                         'cpu': 'u',
                         'memory': 'a'
                        }
        self.meta_json = json.dumps(self.new_meta)

    def tearDown(self):
        self.node.delete()

    def test_create_new_entry_for_node(self):
        url = '/api/environments/1/nodes/new-node.test.com'
        resp = self.client.put(url, json.dumps(self.new_meta), "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name='new-node.test.com')
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.new_meta)

    def test_node_valid_metadata_gets_updated(self):
        resp = self.client.put(self.node_url, json.dumps(self.new_meta), "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.new_meta)

    def test_put_returns_400_if_no_body(self):
        resp = self.client.put(self.node_url, None, "application/json")
        self.assertEquals(resp.status_code, 400)

    def test_put_returns_400_if_wrong_content_type(self):
        resp = self.client.put(self.node_url, self.meta_json, "plain/text")
        self.assertEquals(resp.status_code, 400)

    def test_put_returns_400_if_no_name(self):
        url = '/api/environments/1/nodes/'
        resp = self.client.put(url, self.meta_json, "application/json")
        self.assertEquals(resp.status_code, 400)

    def test_put_returns_400_if_no_block_device_attr(self):
        meta = self.new_meta.copy()
        del meta['block_device']
        resp = self.client.put(self.node_url, json.dumps(meta), "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_put_returns_400_if_no_interfaces_attr(self):
        meta = self.new_meta.copy()
        del meta['interfaces']
        resp = self.client.put(self.node_url, json.dumps(meta), "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_put_returns_400_if_no_cpu_attr(self):
        meta = self.new_meta.copy()
        del meta['cpu']
        resp = self.client.put(self.node_url, json.dumps(meta), "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_put_returns_400_if_no_memory_attr(self):
        meta = self.new_meta.copy()
        del meta['memory']
        resp = self.client.put(self.node_url, json.dumps(meta), "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

