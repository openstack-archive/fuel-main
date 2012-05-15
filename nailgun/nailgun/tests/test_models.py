from django.test import TestCase

from nailgun.models import Node


class TestNodeModel(TestCase):

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
