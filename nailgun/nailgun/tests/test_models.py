from django.test import TestCase

from nailgun.models import Node, Role, Cookbook


class TestNodeModel(TestCase):

    def test_creating_new_node_and_save_to_db(self):
        node = Node()
        node.id = "080000000001"
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


class TestRolesNodesAssociation(TestCase):

    def test_roles_nodes_association(self):
        cook = Cookbook()
        cook.name = 'cookbook'
        cook.version = '1.01.1'
        cook.save()

        role1 = Role()
        role1.id = "myrole"
        role1.cookbook = cook
        role1.name = "My role"
        role1.save()
        role2 = Role()
        role2.id = "myrole2"
        role2.cookbook = cook
        role2.name = "My role 2"
        role2.save()

        node1 = Node()
        node1.id = "080000000001"
        node1.environment_id = 1
        node1.name = "test.example.com"
        node1.save()
        node1.roles = [role1]
        node1.save()
        self.assertEquals(node1.roles.all()[0].id, "myrole")
        self.assertEquals(role1.nodes.all()[0].id, "080000000001")
        self.assertEquals(role1.nodes.all()[0].name, "test.example.com")

        node1.roles.add(role2)
        self.assertEquals(len(node1.roles.all()), 2)

        self.assertEquals(Node.objects.filter(
            roles__id__startswith="myr")[0].id,
                "080000000001")
