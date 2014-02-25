import time
from pageobjects.actions import Actions, DeleteEnvironmentPopup
from pageobjects.environments import Environments, DeployChangesPopup
from pageobjects.nodes import Nodes, RolesPanel
from pageobjects.tabs import Tabs
from tests import preconditions
from tests.base import BaseTestCase
from pageobjects.header import TaskResultAlert


class TestEnvironmentActions(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()

    """Each test precondition

        Steps:
            1. Create environment with default values
            2. Open created environment
            3. Open actions tab
    """

    def setUp(self):
        BaseTestCase.clear_nailgun_database()
        preconditions.Environment.simple_flat()
        Environments().create_cluster_boxes[0].click()
        Tabs().actions.click()

    """Rename environment

        Scenario:
            1. Clear environment name
            2. Enter new name
            3. Click Rename
            4. Verify environment name is changed
    """

    def test_rename(self):
        value = 'Happy environment'
        with Actions() as a:
            a.name.clear()
            a.name.send_keys(value)
            a.rename.click()
            time.sleep(1)
        Tabs().nodes.click()
        self.assertEqual(value, Nodes().env_name.text,
                         'Environment has been renamed')

    """Delete environment

        Scenario:
            1. Click delete environment
            2. Click delete on confirmation pop-up
            3. Verify that environment is deleted
    """

    def test_delete(self):
        with Actions() as a:
            a.delete.click()
            DeleteEnvironmentPopup().delete.click()
            time.sleep(1)
        self.assertEqual(
            0, len(Environments().create_cluster_boxes),
            'Environment has been deleted')

    """Check reset button is inactive

        Scenario:
            1. Check reset button is inactive
    """

    def test_reset_inactive(self):
        self.assertFalse(Actions().reset.is_enabled())

    """Reset simple environment

        Scenario:
            1. Add controller and compute nodes
            2. Deploy claster
            3. Click reset after deploying
            4. Verify that environment is reseted
    """

    def test_simple_reset(self):
        Tabs().nodes.click()
        time.sleep(2)
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

    """Cancel reset environment

        Scenario:
            1. Add controller and compute nodes
            2. Deploy claster
            3. Click reset after deploying and click cancel on popup
            4. Verify that environment isn't reseted
    """

    def test_cancel_reset(self):
        Tabs().nodes.click()
        time.sleep(2)
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

    """Stop deploy

        Scenario:
            1. Add controller and compute nodes
            2. Click deploy
            3. Click stop
            4. Verify that environment isn't deployed
    """

    def test_stop_deploy(self):
        Tabs().nodes.click()
        time.sleep(2)
        Nodes().add_controller_compute_nodes()
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        Actions().cancel_popup.click()
        time.sleep(2)
        Actions().stop_deploy_process()
        for node in Nodes().nodes:
            self.assertEqual(
                'pending addition', node.status.text.lower(),
                'Node status is Pending Addition')
        self.assertTrue(Nodes().deploy_changes.is_enabled())

    """Reset environment after deploy changes

        Scenario:
            1. Add controller and compute nodes
            2. Click deploy
            3. Add new compute node and deploy changes
            4. Reset environment
            4. Verify that environment is reseted
    """

    def test_reset_redeploy(self):
        Tabs().nodes.click()
        time.sleep(2)
        Nodes().add_controller_compute_nodes()
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        TaskResultAlert().close.click()
        Nodes().add_nodes.click()
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().compute.click()
        Nodes().apply_changes.click()
        time.sleep(1)
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

    """Stop and then reset environment

        Scenario:
            1. Add controller and compute nodes
            2. Click deploy
            3. Click stop
            4. Reset environment
            4. Verify that environment is reseted
    """

    def test_stop_reset(self):
        Tabs().nodes.click()
        time.sleep(2)
        Nodes().add_controller_compute_nodes()
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        Actions().cancel_popup.click()
        time.sleep(2)
        Actions().stop_deploy_process()
        Tabs().actions.click()
        time.sleep(1)
        Actions().reset_env()
        Tabs().nodes.click()
        for node in Nodes().nodes:
            self.assertEqual(
                'pending addition', node.status.text.lower(),
                'Node status is Pending Addition')
        self.assertTrue(Nodes().deploy_changes.is_enabled())
