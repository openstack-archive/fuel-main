import mock
from mock import call
from django.test import TestCase
from django.db.models import Model

from nailgun import tasks
from nailgun import models
from nailgun import exceptions


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

        self.assertEquals(self.node.status, "ready")
        res = tasks.bootstrap_node.delay(self.node.id)
        self.assertEquals(res.state, "SUCCESS")
        node = models.Node.objects.get(id=self.node.id)
        self.assertEquals(node.status, "ready")

    @mock.patch('nailgun.tasks.SshConnect')
    def test_bootstrap_calls_provision_and_ssh(self, ssh_mock):
        ssh = ssh_mock.return_value
        ssh.run = mock.MagicMock(return_value=True)
        tasks._provision_node = mock.MagicMock(return_value=None)
        tasks.bootstrap_node(self.node.id)
        self.assertEquals(tasks._provision_node.call_args_list,
                [call(self.node.id)])
        self.assertEquals(ssh.run.call_args_list,
                [call('/opt/nailgun/bin/deploy')])

    @mock.patch('nailgun.tasks.SshConnect')
    def test_bootstrap_does_not_call_provision(self, ssh_mock):
        ssh = ssh_mock.return_value
        ssh.run.return_value = True
        tasks._provision_node = mock.MagicMock(return_value=None)
        tasks.bootstrap_node(self.node.id, installed=True)
        self.assertEquals(tasks._provision_node.call_args_list, [])

    @mock.patch('nailgun.tasks.SshConnect')
    @mock.patch('nailgun.tasks._provision_node')
    def test_bootstrap_raises_deploy_error(self, pn_mock, ssh_mock):
        ssh = ssh_mock.return_value
        ssh.run.return_value = False
        pn_mock.return_value = True

        with self.assertRaises(exceptions.DeployError):
            tasks.bootstrap_node(self.node.id)

    @mock.patch('nailgun.tasks.SshConnect')
    @mock.patch('nailgun.tasks._provision_node')
    def test_bootstrap_puts_error_in_task(self, pn_mock, ssh_mock):
        ssh = ssh_mock.return_value
        ssh.run.return_value = False
        pn_mock.return_value = True

        self.assertEquals(self.node.status, "ready")
        res = tasks.bootstrap_node.delay(self.node.id)
        self.assertEquals(res.state, "FAILURE")
        self.assertIsInstance(res.result, exceptions.DeployError)
        self.assertTrue(res.ready)
        node = models.Node.objects.get(id=self.node.id)
        self.assertEquals(node.status, "error")
