import simplejson as json
from django.test import TestCase
from django import http

from ngui.models import Node
from api.handlers import NodeHandler


class NodeModelTest(TestCase):

    def test_creating_new_node_and_save_to_db(self):
        node = Node()
        node.environment_id = 1
        node.name = "0-test_server.name.com"
        node.metadata = {'metakey': 'metavalue'}

        node.save()

        all_nodes = Node.objects.all()
        self.assertEquals(len(all_nodes), 1)
        self.assertEquals(all_nodes[0], node)

        self.assertEquals(all_nodes[0].name, "0-test_server.name.com")
        self.assertEquals(all_nodes[0].environment_id, 1)
        self.assertEquals(all_nodes[0].metadata,
                {'metakey': 'metavalue'})


class HandlersTest(TestCase):

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

