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

    def setUp(self):
        BaseTestCase.clear_nailgun_database()
        preconditions.Environment.simple_flat()
        Environments().create_cluster_boxes[0].click()
        Tabs().actions.click()

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

    def test_delete(self):
        with Actions() as a:
            a.delete.click()
            DeleteEnvironmentPopup().delete.click()
            time.sleep(1)
        self.assertEqual(
            0, len(Environments().create_cluster_boxes),
            'Environment has been deleted')
