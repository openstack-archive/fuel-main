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
from pageobjects.base import PageObject


class TestConfigureNetworksPage(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        """Global precondition

        Steps:
            1. Create simple environment with default values
            2. Add one controller node
        """
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

    def setUp(self):
        """Each test precondition

        Steps:
            1. Click on created environment
            2. Select controller node
            3. Click Configure Interfaces
        """
        BaseTestCase.setUp(self)
        Environments().create_cluster_boxes[0].click()
        Nodes().nodes[0].details.click()
        NodeInfo().edit_networks.click()

    def test_drag_and_drop(self):
        """Drag and drop networks between interfaces

        Scenario:
            1. Drag and drop Storage network from eth0 to eth1
            2. Drag and drop Management network from eth0 to eth2
            3. Drag and drop VM network from eth0 to eth2
            4. Verify that networks are on correct interfaces
        """
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

    def test_public_floating_grouped(self):
        """Drag and drop public and floating networks

        Scenario:
            1. Drag and drop Public network from eth0 to eth1
            2. Verify that Floating network is moved to eth1 too
            3. Drag and drop Floating network from eth1 to eth2
            4. Verify that Public network is moved to eth2 too
        """
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

    def test_admin_pxe_is_not_dragable(self):
        """Drag and drop Admin(PXE) network

        Scenario:
            1. Drag and drop Admin(PXE) network from eth2 to eth0
            2. Verify that network isn't draggable
        """
        with InterfacesSettings() as s:
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[2].networks['admin (pxe)'],
                s.interfaces[0].networks_box).perform()
            self.assertNotIn(
                'admin (pxe)', s.interfaces[0].networks,
                'admin (pxe) has not been moved')

    def test_two_untagged_on_interface(self):
        """Assign two untagged networks to one interface

        Scenario:
            1. Drag and drop Public network from eth0 to eth2
            2. Verify that eth2 is highlighted with red colour,
               there is error message and Apply button is inactive
            3. Drag and drop Public network from eth2 to eth1
            4. Verify that eth2 isn't highlighted, error message
               has disappeared and Apply button is active
        """
        error = 'Untagged networks can not be assigned to one interface'
        with InterfacesSettings() as s:
            ActionChains(browser.driver).drag_and_drop(
                s.interfaces[0].networks['public'],
                s.interfaces[2].networks_box).perform()
            self.assertIn(
                'nodrag', s.interfaces[2].parent.get_attribute('class'),
                'Red border')
            self.assertIn(
                error,
                s.interfaces[2].parent.find_element_by_xpath('./..').text,
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
                error,
                s.interfaces[2].parent.find_element_by_xpath('./..').text,
                'Error message is displayed'
            )
            self.assertTrue(s.apply.is_enabled(), 'Apply enabled')

    def test_cancel_changes(self):
        """Assign two untagged networks to one interface

        Scenario:
            1. Drag and drop Public network from eth0 to eth1
            2. Drag and drop Storage network from eth0 to eth2
            3. Click Cancel Changes
            4. Verify that Public, Storage, Floating network
               are on eth0 interface
        """
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

    def setUp(self):
        """Each test precondition

        Steps:
            1. Create simple environment with default values
            2. Click on created environment
            3. Create controller node
            4. Select controller node
            5. Click Configure Interfaces
        """
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

    def test_save_load_defaults(self):
        """Load default network settings

        Scenario:
            1. Drag and drop Public network from eth0 to eth1
            2. Drag and drop Storage network from eth0 to eth2
            3. Click Apply
            4. Click Load Defaults
            5. Verify that Public, Storage, Floating network
               are on eth0 interface
        """
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

    def test_configure_interfaces_of_several_nodes(self):
        """Configure interfaces on several nodes

        Scenario:
            1. Add compute node
            2. Select compute and controller node
               and click Configure interfaces
            3. Drag and drop Public network from eth0 to eth1
            4. Drag and drop Storage network from eth0 to eth2
            5. Drag and drop Management network from eth0 to eth1
            6. Click Apply
            7. Verify that Public and Management networks
               are on eth1 interface, Storage is on eth2
        """
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

    def test_vlan_id_labels_visibility(self):
        """Checking vlan id label when vlan tagging is disabled

        Scenario:
            1. Open Networks tab
            2. Disable vlan tagging for Management, Storage, VM(Fixed)
            3. Open Nodes tab
            4. Select controller node
            5. Click configure interfaces
            6. Verify that 'Vlan Id' isn't visible on Storage,
               Management, VM(Fixed) network boxes
        """
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

    def test_vlan_id_values(self):
        """Checking correctness of vlan id on Networks tab

        Scenario:
            1. Open Networks tab
            2. Enable vlan tagging for Management, Storage, VM(Fixed)
               and enter values in range from 110 to 200
            3. Open Nodes tab
            4. Select controller node
            5. Click configure interfaces
            6. Verify that 'Vlan Id' values are correct on Storage,
               Management, VM(Fixed) network boxes
        """
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
                label.format(vlans[0]), s.interfaces[0].
                networks['management'].text,
                'vlan id is correct. Management network')
            self.assertIn(
                label.format(vlans[1]), s.interfaces[0].
                networks['storage'].text,
                'vlan id is correct. Storage network')
            self.assertIn(
                label.format(vlans[2]), s.interfaces[0].
                networks['vm (fixed)'].text,
                'vlan id is correct. VM (Fixed) network')


class TestBondingInterfaces(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()

    def setUp(self):
        """Each test precondition

        Steps:
            1. Create environment with Neutron gre
            2. Open created environment
            3. Add controller node
            4. Open interface configuration of the node
        """
        BaseTestCase.clear_nailgun_database()
        BaseTestCase.setUp(self)
        preconditions.Environment.simple_neutron_gre()
        Environments().create_cluster_boxes[0].click()
        PageObject.click_element(Nodes(), 'add_nodes')
        PageObject.click_element(Nodes(), 'nodes_discovered', 'checkbox', 0)
        RolesPanel().controller.click()
        Nodes().apply_changes.click()
        PageObject.wait_until_exists(Nodes().apply_changes)
        Nodes().nodes[0].details.click()
        NodeInfo().edit_networks.click()

    def test_bond_buttons_inactive(self):
        """Check bond buttons are inactive by default

        Scenario:
            1. Verify bond and unbond buttons are disabled
        """
        PageObject.find_element(InterfacesSettings(), 'bond_interfaces')
        self.assertFalse(InterfacesSettings().bond_interfaces.is_enabled())
        self.assertFalse(InterfacesSettings().unbond_interfaces.is_enabled())

    def test_inactive_one_selected(self):
        """Check bond buttons are inactive if one interface is selected

        Scenario:
            1. Select one interface
            2. Verify bond and unbond buttons are disabled
        """
        with InterfacesSettings() as s:
            s.interfaces[0].interface_checkbox.click()
            self.assertFalse(s.bond_interfaces.is_enabled())
            self.assertFalse(s.unbond_interfaces.is_enabled())

    def test_bond_interfaces(self):
        """Bond two interfaces

        Scenario:
            1. Select two interfaces
            2. Click bond interfaces
            3. Verify that interfaces were bonded
        """
        with InterfacesSettings() as s:
            s.interfaces[0].interface_checkbox.click()
            s.interfaces[1].interface_checkbox.click()
            self.assertTrue(s.bond_interfaces.is_enabled())
            s.bond_interfaces.click()
            s.interfaces[0].bond_mode
            self.assertFalse(s.bond_interfaces.is_enabled())
            self.assertFalse(s.unbond_interfaces.is_enabled())

    def test_cancel_bonding(self):
        """Cancel bonding

        Scenario:
            1. Select two interfaces
            2. Click bond interfaces
            3. Click cancel changes
            4. Verify that interfaces aren't bonded
        """
        with InterfacesSettings() as s:
            s.interfaces[0].interface_checkbox.click()
            s.interfaces[1].interface_checkbox.click()
            s.bond_interfaces.click()
            s.cancel_changes.click()
            self.assertEqual(len(s.interfaces), 3, 'Interfaces amount')

    def test_load_default_bonding(self):
        """Load default bonding

        Scenario:
            1. Select two interfaces
            2. Click bond interfaces
            3. Click load defaults
            4. Verify that interfaces aren't bonded
        """
        with InterfacesSettings() as s:
            s.interfaces[0].interface_checkbox.click()
            s.interfaces[1].interface_checkbox.click()
            s.bond_interfaces.click()
            s.apply.click()
            time.sleep(2)
            self.assertEqual(len(s.interfaces), 2, 'Interfaces amount not 2')
            PageObject.click_element(s, 'load_defaults')
            PageObject.wait_until_exists(s.interfaces[0].bond_mode)
            self.assertEqual(len(s.interfaces), 3, 'Interfaces amount not 3')

    def test_unbond_interfaces(self):
        """Unbond interfaces

        Scenario:
            1. Select two interfaces
            2. Click bond interfaces
            3. Click unbond defaults
            4. Verify that interfaces aren't bonded
        """
        with InterfacesSettings() as s:
            s.interfaces[0].interface_checkbox.click()
            s.interfaces[1].interface_checkbox.click()
            s.bond_interfaces.click()
            s.interfaces[0].interface_checkbox.click()
            s.unbond_interfaces.click()
            self.assertEqual(len(s.interfaces), 3, 'Interfaces amount not 3')

    def test_bond_mode(self):
        """Change bond modes

        Scenario:
            1. Select two interfaces
            2. Click bond interfaces
            3. Change bond modes
            4. Verify that modes are saved correctly
        """
        with InterfacesSettings() as s:
            s.interfaces[0].interface_checkbox.click()
            s.interfaces[1].interface_checkbox.click()
            s.bond_interfaces.click()
            s.interfaces[0].select_mode.select_by_visible_text('Balance SLB')
            self.assertEqual(s.interfaces[0].select_mode.
                             first_selected_option.text,
                             'Balance SLB', 'Text is Balance SLB')
            s.interfaces[0].select_mode.\
                select_by_visible_text('LACP Balance TCP')
            self.assertEqual(s.interfaces[0].select_mode.
                             first_selected_option.text,
                             'LACP Balance TCP', 'Text is LACP Balance TCP')
