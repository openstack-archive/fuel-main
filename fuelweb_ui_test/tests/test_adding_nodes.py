import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from pageobjects.environments import Environments
from pageobjects.header import Header
from pageobjects.nodes import Nodes, NodeInfo, RolesPanel
from pageobjects.tabs import Tabs
from tests import preconditions
from tests.base import BaseTestCase
from tests.test_roles import ROLE_CONTROLLER, ROLE_CEPH, ROLE_CINDER


class TestNodesAddPage(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        """Global precondition

        Steps:
            1. Simple environment with default values is created
        """
        BaseTestCase.setUpClass()
        preconditions.Environment.simple_flat()

    def setUp(self):
        """Each test precondition

        Steps:
            1. Click on created simple environment
            2. Click 'Add nodes'
        """
        BaseTestCase.setUp(self)
        Environments().create_cluster_boxes[0].click()
        time.sleep(1)
        Nodes().add_nodes.click()
        time.sleep(1)

    def test_discovered_nodes_enabled(self):
        """Check that discovered nodes checkboxes are enabled

        Scenario:
            1. Verify discovered nodes checkboxes are active
        """
        with Nodes()as n:
            for node in n.nodes_discovered:
                self.assertTrue(
                    node.checkbox.find_element_by_tag_name('input').
                    is_enabled(),
                    'Node enabled')

    def test_offline_nodes_disabled(self):
        """Check that offline nodes checkboxes are disabled

        Scenario:
            1. Verify offline nodes checkboxes are inactive
        """
        with Nodes()as n:
            for node in n.nodes_offline:
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').
                    is_enabled(),
                    'Node disabled')

    def test_error_nodes_disabled(self):
        """Check that error nodes checkboxes are disabled

        Scenario:
            1. Verify error nodes checkboxes are inactive
        """
        with Nodes()as n:
            for node in n.nodes_error:
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').
                    is_enabled(),
                    'Node disabled')

    def test_select_all(self):
        """Check Select All checkbox

        Scenario:
            1. Click Select All checkbox
            2. Verify that group Select All checkboxes are selected
            3. Verify that discovered nodes checkboxes are selected
            4. Verify that offline and error nodes checkboxes aren't selected
        """
        with Nodes()as n:
            n.select_all.click()
            for selects in n.select_all_in_group:
                self.assertTrue(selects.is_selected(),
                                'Select all in group is selected')
            for node in n.nodes_discovered:
                self.assertTrue(
                    node.checkbox.find_element_by_tag_name('input').
                    is_selected(),
                    'Discovered node is selected')
            for node in n.nodes_offline:
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').
                    is_selected(),
                    'Offline node is not selected')
            for node in n.nodes_error:
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').
                    is_selected(),
                    'Error node is not selected')

    def test_select_all_in_group(self):
        """Check Select All in group

        Scenario:
            1. Click Select All in each group of nodes
            2. Verify that nodes checkboxes are selected
        """
        with Nodes()as n:
            for i, group in enumerate(n.node_groups):
                group.select_all_in_group[0].click()
                for node in group.nodes_discovered:
                    self.assertTrue(
                        node.checkbox.find_element_by_tag_name('input').
                        is_selected(),
                        'Discovered node is selected')
            self.assertTrue(
                n.select_all.is_selected(), '"Select all" is checked')

    def test_select_all_selecting_nodes_one_by_one(self):
        """Check selecting elements one by one

        Scenario:
            1. Select nodes one by one
            2. Verify that Select all checkbox for group is selected
               when all discovered nodes in group are selected
            3. Verify that Select all checkbox is selected when
               all nodes are selected
        """
        with Nodes()as n:
            for i, group in enumerate(n.node_groups):
                for node in group.nodes_discovered:
                    node.checkbox.click()
                self.assertTrue(
                    group.select_all_in_group[0].is_selected(),
                    '"Select all in group" is checked')
            self.assertTrue(
                n.select_all.is_selected(), '"Select all" is checked')

    def test_selecting_nodes_clicking_them_discovered(self):
        """Check selecting discovered elements by clicking on node area

        Scenario:
            1. Select all discovered nodes by clicking on node area
            2. Verify that all discovered nodes are selected
        """
        with Nodes()as n:
            for node in n.nodes_discovered:
                node.parent.click()
                self.assertTrue(
                    node.checkbox.find_element_by_tag_name('input').
                    is_selected(),
                    'Discovered node is selected')

    def test_selecting_nodes_clicking_them_offline(self):
        """Check offline nodes can't be selected by clicking on node area

        Scenario:
            1. Select all offline nodes by clicking on node area
            2. Verify that all offline nodes aren't selected
        """
        with Nodes()as n:
            for node in n.nodes_offline:
                node.parent.click()
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').
                    is_selected(),
                    'Offline node is not selected')

    def test_selecting_nodes_clicking_them_error(self):
        """Check error nodes can't be selected by clicking on node area

        Scenario:
            1. Select all error nodes by clicking on node area
            2. Verify that all error nodes aren't selected
        """
        with Nodes()as n:
            for node in n.nodes_error:
                node.parent.click()
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').
                    is_selected(),
                    'Error node is not selected')

    def test_node_info_popup(self):
        """Check node info in pop-up

        Scenario:
            1. Click edit node
            2. Verify that name in header is the same as on nodes list page
            3. Do this check for discovered, offline, error node
        """
        def test_popup(node):
            node.details.click()
            with NodeInfo() as details:
                self.assertEqual(
                    node.name.text, details.header.text,
                    'Node name')
                details.close.click()
                details.wait_until_exists()

        with Nodes()as n:
            test_popup(n.nodes_discovered[0])
            test_popup(n.nodes_offline[0])
            test_popup(n.nodes_error[0])

    def test_renaming_node(self):
        """Rename node name

        Scenario:
            1. Click on node name
            2. Change name and click on node area - name isn't changed
            3. Click on node name again
            4. Change name and hit enter
            5. Verify that name is correctly changed
        """
        name = 'new node name'
        with Nodes()as n:
            old_name = n.nodes_discovered[0].name.text
            n.nodes_discovered[0].name.click()
            self.assertTrue(
                n.nodes_discovered[0].name_input.is_displayed(),
                'input visible')
            n.nodes_discovered[0].name_input.send_keys(name)
            n.nodes_discovered[0].parent.click()
            self.assertRaises(
                NoSuchElementException, getattr, n.nodes_discovered[0],
                'name_input')
            self.assertEqual(
                old_name, n.nodes_discovered[0].name.text,
                'Node has old name')
            n.nodes_discovered[0].name.click()
            n.nodes_discovered[0].name_input.send_keys(name)
            n.nodes_discovered[0].name_input.send_keys(Keys.ENTER)
            time.sleep(2)
        self.assertEqual(
            name, Nodes().nodes_discovered[0].name.text,
            'New node name')


class TestAddingNodes(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()

    def setUp(self):
        """Each test precondition

        Steps:
            1. Create simple environment with default values
            2. Click on created simple environment
            2. Click 'Add nodes'
        """
        BaseTestCase.clear_nailgun_database()
        preconditions.Environment.simple_flat()
        BaseTestCase.setUp(self)
        Environments().create_cluster_boxes[0].click()
        time.sleep(1)
        Nodes().add_nodes.click()
        time.sleep(1)

    def test_adding_node_single_role(self):
        """Add one controller node

        Scenario:
            1. Select Controller role and select node
            2. Click Apply Changes
            3. Verify that Nodes page is open
            4. Amount of nodes is 1
            5. Node is the same that was selected
            6. Role of node is Controller
        """
        name = Nodes().nodes_discovered[0].name.text
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().controller.click()
        Nodes().apply_changes.click()
        time.sleep(1)
        with Nodes() as n:
            self.assertTrue(n.env_name.is_displayed())
            self.assertEqual(len(n.nodes), 1, 'Nodes amount')
            self.assertEqual(n.nodes[0].name.text, name, 'Node name')
            self.assertIn(ROLE_CONTROLLER, n.nodes[0].roles.text, 'Node role')

    def test_adding_node_multiple_roles(self):
        """Add node with controller, cinder, ceph roles

        Scenario:
            1. Select Controller, Cinder, Ceph roles and select node
            2. Click Apply Changes
            3. Verify that Nodes page is open
            4. Role of node is Controller, Cinder, Ceph
        """
        Nodes().nodes_discovered[0].checkbox.click()
        with RolesPanel() as r:
            r.controller.click()
            r.cinder.click()
            r.ceph_osd.click()
        Nodes().apply_changes.click()
        time.sleep(1)
        with Nodes() as n:
            self.assertTrue(n.env_name.is_displayed())
            self.assertIn(ROLE_CONTROLLER, n.nodes[0].roles.text,
                          'Node first role')
            self.assertIn(ROLE_CINDER, n.nodes[0].roles.text,
                          'Node second role')
            self.assertIn(ROLE_CEPH, n.nodes[0].roles.text,
                          'Node third role')

    def test_edit_role_add_new_role(self):
        """Edit node by adding new role to it

        Scenario:
            1. Select Controller role and select node
            2. Click Apply Changes
            3. Select added node and click Edit Roles
            4. Select Cinder Role and click Apply Changes
            5. Verify that roles of node are Controller, Cinder
        """
        # Add node with controller role
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().controller.click()
        Nodes().apply_changes.click()
        time.sleep(1)
        # Add cinder role
        with Nodes() as n:
            n.nodes[0].checkbox.click()
            n.edit_roles.click()
        RolesPanel().cinder.click()
        Nodes().apply_changes.click()
        time.sleep(1)
        with Nodes() as n:
            self.assertIn(ROLE_CONTROLLER, n.nodes[0].roles.text,
                          'Controller role')
            self.assertIn(ROLE_CINDER, n.nodes[0].roles.text,
                          'Cinder role')

    def test_edit_role_change_role(self):
        """Edit node by removing old role and adding two new roles to it

        Scenario:
            1. Select Controller role and select node
            2. Click Apply Changes
            3. Select added node and click Edit Roles
            4. Unselect Controller and select Cinder and Ceph Role
            5. Click Apply Changes
            6. Verify that roles of node are Cinder and Ceph
        """
        # Add node with controller role
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().controller.click()
        Nodes().apply_changes.click()
        time.sleep(1)
        # Remove controller, Add cinder and ceph-osd roles
        with Nodes() as n:
            n.nodes[0].checkbox.click()
            n.edit_roles.click()
        with RolesPanel() as r:
            r.controller.click()
            r.cinder.click()
            r.ceph_osd.click()
        Nodes().apply_changes.click()
        time.sleep(1)
        with Nodes() as n:
            self.assertNotIn(ROLE_CONTROLLER, n.nodes[0].roles.text,
                             'Controller role has been removed')
            self.assertIn(ROLE_CINDER, n.nodes[0].roles.text,
                          'Cinder role')
            self.assertIn(ROLE_CEPH, n.nodes[0].roles.text,
                          'Ceph-osd role')

    def test_unallocated_nodes_counter(self):
        """Unallocated nodes counter

        Scenario:
            1. Add new node with compute role
            2. Verify that number of unallocated nodes was reduced on 1
        """
        initial = int(Header().unallocated_nodes.text)
        discovered = len(Nodes().nodes_discovered)

        Tabs().nodes.click()
        for i in range(discovered):
            time.sleep(1)
            Nodes().add_nodes.click()
            time.sleep(1)
            Nodes().nodes_discovered[0].checkbox.click()
            RolesPanel().compute.click()
            Nodes().apply_changes.click()
            time.sleep(1)

            self.assertEqual(
                str(initial - i - 1), Header().unallocated_nodes.text,
                'Unallocated nodes amount')


class TestGroupBy(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        """Global precondition

        Steps:
            1. Create simple environment with default values
            2. Add one controller node
            3. Add other nodes as compute
        """
        BaseTestCase.setUpClass()
        BaseTestCase.get_home()
        preconditions.Environment().simple_flat()
        Environments().create_cluster_boxes[0].click()
        time.sleep(1)

        # Add controller
        Nodes().add_nodes.click()
        time.sleep(1)
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().controller.click()
        Nodes().apply_changes.click()
        time.sleep(1)

        # Add other discovered nodes as compute
        Nodes().add_nodes.click()
        time.sleep(1)
        for n in Nodes().nodes_discovered:
            n.checkbox.click()
        RolesPanel().compute.click()
        Nodes().apply_changes.click()

    def setUp(self):
        """Each test precondition

        Steps:
            1. Click on created environment
        """
        BaseTestCase.setUp(self)
        Environments().create_cluster_boxes[0].click()

    def _test_group_by(self, group_by, nodes_in_groups):
        with Nodes() as n:
            time.sleep(1)
            n.group_by.select_by_visible_text(group_by)
            time.sleep(1)
            self.assertEqual(len(nodes_in_groups),
                             len(n.node_groups), 'Groups amount')
            for i, group in enumerate(n.node_groups):
                self.assertEqual(
                    nodes_in_groups[i], len(group.nodes),
                    'Group #{0} has {1} nodes'.format(i, nodes_in_groups[i]))

    def test_group_by_roles(self):
        """Group nodes by role

        Scenario:
            1. Select Roles value in Group By list
            2. Verify that there are 2 groups with
               correct number of nodes in each group
        """
        self._test_group_by('Roles', [1, 5])

    def test_group_by_hardware_info(self):
        """Group nodes by hardware

        Scenario:
            1. Select Hardware Info value in Group By list
            2. Verify that there are 5 groups with
               correct number of nodes in each group
        """
        self._test_group_by('Hardware Info', [1, 1, 2, 1, 1])

    def test_group_by_roles_and_hardware_info(self):
        """Group nodes by role and hardware info

        Scenario:
            1. Select Roles and hardware info value in Group By list
            2. Verify that there are 6 groups with
               correct number of nodes in each group
        """
        self._test_group_by('Roles and hardware info', [1, 2, 1, 1, 1])
