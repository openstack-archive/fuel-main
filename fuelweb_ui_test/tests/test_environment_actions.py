import time
from pageobjects.actions import Actions, DeleteEnvironmentPopup
from pageobjects.environments import Environments, DeployChangesPopup
from pageobjects.nodes import Nodes, RolesPanel
from pageobjects.tabs import Tabs
from tests import preconditions
from tests.base import BaseTestCase
from pageobjects.header import TaskResultAlert
from pageobjects.base import PageObject


class TestEnvironmentActions(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()

    def setUp(self):
        """Each test precondition

        Steps:
            1. Create environment with default values
            2. Open created environment
            3. Open actions tab
        """
        BaseTestCase.clear_nailgun_database()
        preconditions.Environment.simple_flat()
        Environments().create_cluster_boxes[0].click()
        Tabs().actions.click()

    def test_rename(self):
        """Rename environment

        Scenario:
            1. Clear environment name
            2. Enter new name
            3. Click Rename
            4. Verify environment name is changed
        """
        value = 'Happy environment'
        with Actions() as a:
            a.name.clear()
            a.name.send_keys(value)
            a.rename.click()
            time.sleep(1)
        Tabs().nodes.click()
        self.assertEqual(value, Nodes().env_name.text,
                         'Environment has been renamed')

    def test_delete(self):
        """Delete environment

        Scenario:
            1. Click delete environment
            2. Click delete on confirmation pop-up
            3. Verify that environment is deleted
        """
        with Actions() as a:
            a.delete.click()
            DeleteEnvironmentPopup().delete.click()
            time.sleep(1)
        self.assertEqual(
            0, len(Environments().create_cluster_boxes),
            'Environment has been deleted')

    def test_reset_inactive(self):
        """Check reset button is inactive

        Scenario:
            1. Check reset button is inactive
        """
        self.assertFalse(Actions().reset.is_enabled())

    def test_simple_reset(self):
        """Reset simple environment

        Scenario:
            1. Add controller and compute nodes
            2. Deploy claster
            3. Click reset after deploying
            4. Verify that environment is reseted
        """
        Tabs().nodes.click()
        Nodes().add_controller_compute_nodes()
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        TaskResultAlert().close.click()
        Tabs().actions.click()
        Actions().reset_env()
        Tabs().nodes.click()
        for node in Nodes().nodes:
            self.assertEqual(
                'pending addition', node.status.text.lower(),
                'Node status is Pending Addition')
        self.assertTrue(Nodes().deploy_changes.is_enabled())

    def test_cancel_reset(self):
        """Cancel reset environment

        Scenario:
            1. Add controller and compute nodes
            2. Deploy claster
            3. Click reset after deploying and click cancel on popup
            4. Verify that environment isn't reseted
        """
        Tabs().nodes.click()
        Nodes().add_controller_compute_nodes()
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        TaskResultAlert().close.click()
        Tabs().actions.click()
        Actions().cancel_reset()
        Tabs().nodes.click()
        for node in Nodes().nodes:
            self.assertEqual(
                'ready', node.status.text.lower(),
                'Node status is Ready')
        Actions().verify_disabled_deploy

    def test_stop_deploy(self):
        """Stop deploy

        Scenario:
            1. Add controller and compute nodes
            2. Click deploy
            3. Click stop
            4. Verify that environment isn't deployed
        """
        Tabs().nodes.click()
        Nodes().add_controller_compute_nodes()
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        Actions().cancel_popup.click()
        Actions().stop_deploy_process()
        PageObject.find_element(Nodes(), 'nodes', 'status', 0)
        for node in Nodes().nodes:
            self.assertEqual(
                'pending addition', node.status.text.lower(),
                'Node status is Pending Addition')
        self.assertTrue(Nodes().deploy_changes.is_enabled())

    def test_reset_redeploy(self):
        """Reset environment after deploy changes

        Scenario:
            1. Add controller and compute nodes
            2. Click deploy
            3. Add new compute node and deploy changes
            4. Reset environment
            4. Verify that environment is reseted
        """
        Tabs().nodes.click()
        Nodes().add_controller_compute_nodes()
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        TaskResultAlert().close.click()
        Nodes().add_nodes.click()
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().compute.click()
        Nodes().apply_changes.click()
        PageObject.wait_until_exists(Nodes().apply_changes)
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        TaskResultAlert().close.click()
        Tabs().actions.click()
        Actions().reset_env()
        Tabs().nodes.click()
        for node in Nodes().nodes:
            self.assertEqual(
                'pending addition', node.status.text.lower(),
                'Node status is Pending Addition')
        self.assertTrue(Nodes().deploy_changes.is_enabled())

    def test_stop_reset(self):
        """Stop and then reset environment

        Scenario:
            1. Add controller and compute nodes
            2. Click deploy
            3. Click stop
            4. Reset environment
            4. Verify that environment is reseted
        """
        Tabs().nodes.click()
        Nodes().add_controller_compute_nodes()
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        Actions().cancel_popup.click()
        Actions().stop_deploy_process()
        Tabs().actions.click()
        Actions().reset_env()
        Tabs().nodes.click()
        for node in Nodes().nodes:
            self.assertEqual(
                'pending addition', node.status.text.lower(),
                'Node status is Pending Addition')
        self.assertTrue(Nodes().deploy_changes.is_enabled())
