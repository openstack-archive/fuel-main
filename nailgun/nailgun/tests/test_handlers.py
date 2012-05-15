import simplejson as json
from django import http
from django.test import TestCase

from nailgun.models import Node


class TestHandlers(TestCase):

    def setUp(self):
        self.request = http.HttpRequest()

        self.node = Node(environment_id=1,
                    name="test.server.com",
                    metadata={'key': 'value', 'key2': 'val2'})
        self.node.save()
        self.node_url = '/api/environments/1/nodes/test.server.com'

    def tearDown(self):
        self.node.delete()

    def test_node_metadata_gets_updated(self):
        new_meta = {'key': 'new-val', 'abc': 'd'}

        self.client.put(self.node_url, json.dumps(new_meta), "application/json")

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name='test.server.com')
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, {'key': 'new-val', 'abc': 'd'})

    def test_put_returns_400_if_no_body(self):
        resp = self.client.put(self.node_url, None, "application/json")

        self.assertEquals(resp.status_code, 400)

