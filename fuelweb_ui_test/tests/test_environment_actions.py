import time
from pageobjects.actions import Actions, DeleteEnvironmentPopup
from pageobjects.environments import Environments
from pageobjects.nodes import Nodes
from pageobjects.tabs import Tabs
from tests import preconditions
from tests.base import BaseTestCase


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
