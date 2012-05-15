import simplejson as json
from django import http
from django.test import TestCase

from nailgun.models import Node
from nailgun.api.handlers import NodeHandler


class TestHandlers(TestCase):

    def test_node_metadata_gets_updated(self):
        self.request = http.HttpRequest()

        node = Node(environment_id=1,
                    name="test.server.com",
                    metadata={'key': 'value', 'key2': 'val2'})
        node.save()

        handler = NodeHandler()
        new_meta = {'key': 'new-val', 'abc': 'd'}

        nodes_url = '/api/environments/1/nodes/test.server.com'
        self.client.put(nodes_url, json.dumps(new_meta), "application/json")

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name='test.server.com')
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, {'key': 'new-val', 'abc': 'd'})

