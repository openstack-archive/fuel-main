import time
from selenium.webdriver import ActionChains
import browser
from pageobjects.environments import Environments, DeployChangesPopup
from pageobjects.header import TaskResultAlert
from pageobjects.node_disks_settings import DisksSettings
from pageobjects.node_interfaces_settings import InterfacesSettings
from pageobjects.nodes import Nodes, RolesPanel, DeleteNodePopup, NodeInfo
from tests import preconditions
from tests.base import BaseTestCase


class TestDeploy(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()

    def setUp(self):
        """Each test precondition

        Steps:
            1. Create simple environment with default values
            2. Click on created environment
        """
        BaseTestCase.clear_nailgun_database()
        BaseTestCase.setUp(self)
        preconditions.Environment.simple_flat()
        Environments().create_cluster_boxes[0].click()
        time.sleep(1)

    def test_add_nodes(self):
        """Deploy environment with controller and compute nodes

        Scenario:
            1. Add controller and compute node
            2. Deploy changes
            3. Verify that nodes statuses are ready
        """
        Nodes().add_nodes.click()
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().controller.click()
        Nodes().apply_changes.click()
        time.sleep(2)
        Nodes().add_nodes.click()
        time.sleep(1)
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().compute.click()
        Nodes().apply_changes.click()
        time.sleep(1)

        for node in Nodes().nodes:
            self.assertEqual(
                'pending addition', node.status.text.lower(),
                'Node status is Pending Addition')

        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        TaskResultAlert().close.click()

        with Nodes() as n:
            self.assertEqual(2, len(n.nodes), 'Nodes amount')
            for node in n.nodes:
                self.assertEqual('ready', node.status.text.lower(),
                                 'Node status is READY')

    def test_delete_node(self):
        """Delete one node and deploy changes

        Scenario:
            1. Add controller and compute node
            2. Deploy changes
            3. Delete one node
            4. Deploy changes
            5. Verify that only one node is present
        """
        self.test_add_nodes()

        with Nodes() as n:
            n.nodes[1].checkbox.click()
            n.delete_nodes.click()
        with DeleteNodePopup() as p:
            p.delete.click()
            p.wait_until_exists()
            time.sleep(1)

        self.assertEqual(
            'pending deletion', Nodes().nodes[1].status.text.lower(),
            'Node status is Pending Deletion')

        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        TaskResultAlert().close.click()

        with Nodes() as n:
            self.assertEqual(1, len(n.nodes), 'Nodes amount')
            for node in n.nodes:
                self.assertEqual('ready', node.status.text.lower(),
                                 'Node status is READY')

    def test_node_configure_networks_is_readonly(self):
        """Configure network interfaces after deploy

        Scenario:
            1. Add controller node
            2. Deploy changes
            3. Select controller node and click configure interfaces
            4. Drag and drop Storage network to eth1
            5. Verify that Storage network can't be dragged and dropped
            6. Apply, Load defaults, Cancel Changes buttons are not active
        """
        Nodes().add_nodes.click()
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().controller.click()
        Nodes().apply_changes.click()
        time.sleep(2)
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        time.sleep(1)

        Nodes().nodes[0].details.click()
        NodeInfo().edit_networks.click()

        with InterfacesSettings() as s:
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['storage'],
                s.interfaces[1].networks_box).perform()

            time.sleep(1)
            self.assertNotIn(
                'storage', s.interfaces[1].networks,
                'storage at eht1')
            self.assertFalse(s.apply.is_enabled(), 'Apply is disabled')
            self.assertFalse(s.load_defaults.is_enabled(),
                             'Load defaults is disabled')
            self.assertFalse(s.cancel_changes.is_enabled(),
                             'Cancel changes is disabled')

    def test_node_configure_disks_is_readonly(self):
        """Configure disks after deploy

        Scenario:
            1. Add controller node
            2. Deploy changes
            3. Select controller node and click configure disks
            4. Verify that volume inputs are disabled
            6. Apply, Load defaults, Cancel Changes buttons are not active
        """
        Nodes().add_nodes.click()
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().controller.click()
        Nodes().apply_changes.click()
        time.sleep(2)
        Nodes().deploy_changes.click()
        DeployChangesPopup().deploy.click()
        time.sleep(1)

        Nodes().nodes[0].details.click()
        NodeInfo().edit_disks.click()
        time.sleep(1)

        with DisksSettings() as s:
            for i in range(2):
                self.assertFalse(
                    s.disks[i].volume_group_os.input.is_enabled(),
                    'Base system input is disabled at disk #{0}'.format(i))
                self.assertFalse(
                    s.disks[i].volume_group_image.input.is_enabled(),
                    'Image storage input is disabled at disk #{0}'.format(i))
            self.assertFalse(s.apply.is_enabled(), 'Apply is disabled')
            self.assertFalse(s.load_defaults.is_enabled(),
                             'Load defaults is disabled')
            self.assertFalse(s.cancel_changes.is_enabled(),
                             'Cancel changes is disabled')
