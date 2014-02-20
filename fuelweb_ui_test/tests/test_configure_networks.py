import random
import time
from selenium.webdriver import ActionChains
import browser
from pageobjects.environments import Environments
from pageobjects.networks import Networks
from pageobjects.node_interfaces_settings import InterfacesSettings
from pageobjects.nodes import Nodes, RolesPanel, NodeInfo
from pageobjects.tabs import Tabs
from tests import preconditions
from tests.base import BaseTestCase


class TestConfigureNetworksPage(BaseTestCase):

    """Global precondition

        Steps:
            1. Create simple environment with default values
            2. Add one controller node
    """

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()
        preconditions.Environment.simple_flat()
        Environments().create_cluster_boxes[0].click()
        time.sleep(1)
        Nodes().add_nodes.click()
        time.sleep(1)
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().controller.click()
        Nodes().apply_changes.click()
        time.sleep(1)

    """Each test precondition

        Steps:
            1. Click on created environment
            2. Select controller node
            3. Click Configure Interfaces
    """

    def setUp(self):
        BaseTestCase.setUp(self)
        Environments().create_cluster_boxes[0].click()
        Nodes().nodes[0].details.click()
        NodeInfo().edit_networks.click()

    """Drag and drop networks between interfaces

        Scenario:
            1. Drag and drop Storage network from eth0 to eth1
            2. Drag and drop Management network from eth0 to eth2
            3. Drag and drop VM network from eth0 to eth2
            4. Verify that networks are on correct interfaces
    """

    def test_drag_and_drop(self):
        with InterfacesSettings() as s:
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['storage'],
                s.interfaces[1].networks_box).perform()
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['management'],
                s.interfaces[2].networks_box).perform()
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['vm (fixed)'],
                s.interfaces[2].networks_box).perform()

            self.assertIn(
                'storage', s.interfaces[1].networks,
                'storage at eht1')
            self.assertIn(
                'management', s.interfaces[2].networks,
                'management at eht2')
            self.assertIn(
                'vm (fixed)', s.interfaces[2].networks,
                'vm (fixed) at eht2')

    """Drag and drop public and floating networks

        Scenario:
            1. Drag and drop Public network from eth0 to eth1
            2. Verify that Floating network is moved to eth1 too
            3. Drag and drop Floating network from eth1 to eth2
            4. Verify that Public network is moved to eth2 too
    """

    def test_public_floating_grouped(self):
        with InterfacesSettings() as s:
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['public'],
                s.interfaces[1].networks_box).perform()
            self.assertIn(
                'floating', s.interfaces[1].networks,
                'Floating has been moved')
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[1].networks['floating'],
                s.interfaces[2].networks_box).perform()
            self.assertIn(
                'public', s.interfaces[2].networks,
                'Public has been moved')

    """Drag and drop Admin(PXE) network

        Scenario:
            1. Drag and drop Admin(PXE) network from eth2 to eth0
            2. Verify that network isn't draggable
    """

    def test_admin_pxe_is_not_dragable(self):
        with InterfacesSettings() as s:
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[2].networks['admin (pxe)'],
                s.interfaces[0].networks_box).perform()
            self.assertNotIn(
                'admin (pxe)', s.interfaces[0].networks,
                'admin (pxe) has not been moved')

    """Assign two untagged networks to one interface

        Scenario:
            1. Drag and drop Public network from eth0 to eth2
            2. Verify that eth2 is highlighted with red colour, there is error message and Apply button is inactive
            3. Drag and drop Public network from eth2 to eth1
            4. Verify that eth2 isn't highlighted, error message has disappeared and Apply button is active
    """

    def test_two_untagged_on_interface(self):
        error = 'Untagged networks can not be assigned to one interface'
        with InterfacesSettings() as s:
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['public'],
                s.interfaces[2].networks_box).perform()
            self.assertIn(
                'nodrag', s.interfaces[2].parent.get_attribute('class'),
                'Red border')
            self.assertIn(
                error, s.interfaces[2].parent.find_element_by_xpath('./..').text,
                'Error message is displayed'
            )
            self.assertFalse(s.apply.is_enabled(), 'Apply disabled')
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[2].networks['public'],
                s.interfaces[1].networks_box).perform()
            self.assertNotIn(
                'nodrag', s.interfaces[2].parent.get_attribute('class'),
                'Red border')
            self.assertNotIn(
                error, s.interfaces[2].parent.find_element_by_xpath('./..').text,
                'Error message is displayed'
            )
            self.assertTrue(s.apply.is_enabled(), 'Apply enabled')

    """Assign two untagged networks to one interface

        Scenario:
            1. Drag and drop Public network from eth0 to eth1
            2. Drag and drop Storage network from eth0 to eth2
            3. Click Cancel Changes
            4. Verify that Public, Storage, Floating network are on eth0 interface
    """

    def test_cancel_changes(self):
        with InterfacesSettings() as s:
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['public'],
                s.interfaces[1].networks_box).perform()
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['storage'],
                s.interfaces[2].networks_box).perform()

            s.cancel_changes.click()
            time.sleep(1)
            self.assertIn(
                'storage', s.interfaces[0].networks,
                'storage at eht0')
            self.assertIn(
                'public', s.interfaces[0].networks,
                'public at eht0')
            self.assertIn(
                'floating', s.interfaces[0].networks,
                'floating at eht0')


class TestConfigureNetworks(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()

    """Each test precondition

        Steps:
            1. Create simple environment with default values
            2. Click on created environment
            3. Create controller node
            4. Select controller node
            5. Click Configure Interfaces
    """

    def setUp(self):
        BaseTestCase.clear_nailgun_database()
        BaseTestCase.setUp(self)

        preconditions.Environment.simple_flat()
        Environments().create_cluster_boxes[0].click()
        time.sleep(1)
        Nodes().add_nodes.click()
        time.sleep(1)
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().controller.click()
        Nodes().apply_changes.click()
        time.sleep(1)
        Nodes().nodes[0].details.click()
        NodeInfo().edit_networks.click()

    """Load default network settings

        Scenario:
            1. Drag and drop Public network from eth0 to eth1
            2. Drag and drop Storage network from eth0 to eth2
            3. Click Apply
            4. Click Load Defaults
            5. Verify that Public, Storage, Floating network are on eth0 interface
    """

    def test_save_load_defaults(self):
        with InterfacesSettings() as s:
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['public'],
                s.interfaces[1].networks_box).perform()
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['storage'],
                s.interfaces[2].networks_box).perform()
            s.apply.click()
            time.sleep(1)
        self.refresh()
        with InterfacesSettings() as s:
            self.assertIn(
                'storage', s.interfaces[2].networks,
                'storage at eht2')
            self.assertIn(
                'public', s.interfaces[1].networks,
                'public at eht1')
            self.assertIn(
                'floating', s.interfaces[1].networks,
                'floating at eht1')
            s.load_defaults.click()
            time.sleep(1)
            self.assertIn(
                'storage', s.interfaces[0].networks,
                'storage at eht0')
            self.assertIn(
                'public', s.interfaces[0].networks,
                'public at eht0')
            self.assertIn(
                'floating', s.interfaces[0].networks,
                'floating at eht0')

    """Configure interfaces on several nodes

        Scenario:
            1. Add compute node
            2. Select compute and controller node and click Configure interfaces
            3. Drag and drop Public network from eth0 to eth1
            4. Drag and drop Storage network from eth0 to eth2
            5. Drag and drop Management network from eth0 to eth1
            6. Click Apply
            7. Verify that Public and Management networks are on eth1 interface, Storage is on eth2
    """

    def test_configure_interfaces_of_several_nodes(self):
        # Go back to nodes page
        Tabs().nodes.click()
        # Add second node
        time.sleep(1)
        Nodes().add_nodes.click()
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().compute.click()
        Nodes().apply_changes.click()
        time.sleep(1)
        # rearrange interfaces
        with Nodes() as n:
            n.select_all.click()
            n.configure_interfaces.click()
        with InterfacesSettings() as s:
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['public'],
                s.interfaces[1].networks_box).perform()
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['management'],
                s.interfaces[1].networks_box).perform()
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['storage'],
                s.interfaces[2].networks_box).perform()
            s.apply.click()
            time.sleep(1)

        for i in range(2):
            # Go to nodes page
            Tabs().nodes.click()
            # Verify interfaces settings of each node
            Nodes().nodes[i].details.click()
            NodeInfo().edit_networks.click()
            self.assertIn(
                'public', s.interfaces[1].networks,
                'public at eht1. Node #{0}'.format(i))
            self.assertIn(
                'management', s.interfaces[1].networks,
                'management at eht1. Node #{0}'.format(i))
            self.assertIn(
                'storage', s.interfaces[2].networks,
                'storage at eht2. Node #{0}'.format(i))

    """Checking vlan id label when vlan tagging is disabled

        Scenario:
            1. Open Networks tab
            2. Disable vlan tagging for Management, Storage, VM(Fixed)
            3. Open Nodes tab
            4. Select controller node
            5. Click configure interfaces
            6. Verify that 'Vlan Id' isn't visible on Storage, Management, VM(Fixed) network boxes
    """

    def test_vlan_id_labels_visibility(self):
        label = 'VLAN ID'
        Tabs().networks.click()
        with Networks() as n:
            n.management.vlan_tagging.click()
            n.storage.vlan_tagging.click()
            n.fixed.vlan_tagging.click()
            n.save_settings.click()
            time.sleep(1)
        Tabs().nodes.click()
        Nodes().nodes[0].details.click()
        NodeInfo().edit_networks.click()
        with InterfacesSettings() as s:
            self.assertNotIn(
                label, s.interfaces[0].networks['storage'].text,
                'vlan id is visible. Storage network')
            self.assertNotIn(
                label, s.interfaces[0].networks['management'].text,
                'vlan id is visible. Management network')
            self.assertNotIn(
                label, s.interfaces[0].networks['vm (fixed)'].text,
                'vlan id is visible. VM (Fixed) network')

    """Checking correctness of vlan id on Networks tab

        Scenario:
            1. Open Networks tab
            2. Enable vlan tagging for Management, Storage, VM(Fixed) and enter values in range from 110 to 200
            3. Open Nodes tab
            4. Select controller node
            5. Click configure interfaces
            6. Verify that 'Vlan Id' values are correct on Storage, Management, VM(Fixed) network boxes
    """

    def test_vlan_id_values(self):
        label = 'VLAN ID: {0}'
        vlans = [random.randint(110, 200) for i in range(3)]
        Tabs().networks.click()
        with Networks() as n:
            n.management.vlan_id.clear()
            n.management.vlan_id.send_keys(vlans[0])

            n.storage.vlan_id.clear()
            n.storage.vlan_id.send_keys(vlans[1])

            n.fixed.vlan_id.clear()
            n.fixed.vlan_id.send_keys(vlans[2])

            n.save_settings.click()
            time.sleep(1)

        Tabs().nodes.click()
        Nodes().nodes[0].details.click()
        NodeInfo().edit_networks.click()
        with InterfacesSettings() as s:
            self.assertIn(
                label.format(vlans[0]), s.interfaces[0].networks['management'].text,
                'vlan id is correct. Management network')
            self.assertIn(
                label.format(vlans[1]), s.interfaces[0].networks['storage'].text,
                'vlan id is correct. Storage network')
            self.assertIn(
                label.format(vlans[2]), s.interfaces[0].networks['vm (fixed)'].text,
                'vlan id is correct. VM (Fixed) network')