import mock
from django.test import TestCase
from django.db.models import Model

from nailgun import tasks
from nailgun import models


class TestTasks(TestCase):

    def setUp(self):
        self.node = models.Node(id="080000000001",
                    cluster_id=1,
                    name="test.example.com",
                    ip="127.0.0.1",
                    metadata={})
        self.node.save()

        self.recipe = models.Recipe()
        self.recipe.recipe = 'cookbook::recipe@2.1'
        self.recipe.save()

        self.role = models.Role()
        self.role.save()
        self.role.recipes = [self.recipe]
        self.role.name = "My role"
        self.role.save()

        self.node.roles = [self.role]
        self.node.save()

    def tearDown(self):
        self.node.delete()
        self.role.delete()
        self.recipe.delete()

    @mock.patch('nailgun.tasks.SshConnect')
    @mock.patch('nailgun.tasks._provision_node')
    def test_bootstrap_node(self, pn_mock, ssh_mock):
        ssh = ssh_mock.return_value
        ssh.run.return_value = True
        pn_mock.return_value = True

        self.assertEquals(self.node.status, "online")
        res = tasks.bootstrap_node.delay(self.node.id)
        self.assertEquals(res.state, "SUCCESS")
        node = models.Node.objects.get(id=self.node.id)
        self.assertEquals(node.status, "ready")
