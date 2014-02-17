import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from pageobjects.base import PageObject
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
        BaseTestCase.setUpClass()
        preconditions.Environment.simple_flat()

    def setUp(self):
        BaseTestCase.setUp(self)
        Environments().create_cluster_boxes[0].click()
        Nodes().add_nodes.click()
        time.sleep(1)

    def test_discovered_nodes_enabled(self):
        with Nodes()as n:
            for node in n.nodes_discovered:
                self.assertTrue(
                    node.checkbox.find_element_by_tag_name('input').is_enabled(),
                    'Node enabled')

    def test_offline_nodes_disabled(self):
        with Nodes()as n:
            for node in n.nodes_offline:
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').is_enabled(),
                    'Node disabled')

    def test_error_nodes_disabled(self):
        with Nodes()as n:
            for node in n.nodes_error:
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').is_enabled(),
                    'Node disabled')

    def test_select_all(self):
        with Nodes()as n:
            n.select_all.click()
            for selects in n.select_all_in_group:
                self.assertTrue(selects.is_selected(),
                                'Select all in group is selected')
            for node in n.nodes_discovered:
                self.assertTrue(
                    node.checkbox.find_element_by_tag_name('input').is_selected(),
                    'Discovered node is selected')
            for node in n.nodes_offline:
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').is_selected(),
                    'Offline node is not selected')
            for node in n.nodes_error:
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').is_selected(),
                    'Error node is not selected')

    def test_select_all_in_group(self):
        with Nodes()as n:
            for i, group in enumerate(n.node_groups):
                group.select_all_in_group[0].click()
                for node in group.nodes_discovered:
                    self.assertTrue(
                    node.checkbox.find_element_by_tag_name('input').is_selected(),
                    'Discovered node is selected')
            self.assertTrue(
                n.select_all.is_selected(), '"Select all" is checked')

    def test_select_all_selecting_nodes_one_by_one(self):
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
        with Nodes()as n:
            for node in n.nodes_discovered:
                node.parent.click()
                self.assertTrue(
                    node.checkbox.find_element_by_tag_name('input').is_selected(),
                    'Discovered node is selected')

    def test_selecting_nodes_clicking_them_offline(self):
        with Nodes()as n:
            for node in n.nodes_offline:
                node.parent.click()
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').is_selected(),
                    'Offline node is not selected')

    def test_selecting_nodes_clicking_them_error(self):
        with Nodes()as n:
            for node in n.nodes_error:
                node.parent.click()
                self.assertFalse(
                    node.checkbox.find_element_by_tag_name('input').is_selected(),
                    'Error node is not selected')

    def test_node_info_popup(self):
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
        BaseTestCase.clear_nailgun_database()
        preconditions.Environment.simple_flat()
        BaseTestCase.setUp(self)
        Environments().create_cluster_boxes[0].click()
        Nodes().add_nodes.click()
        time.sleep(1)

    def test_adding_node_single_role(self):
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
        initial = int(Header().unallocated_nodes.text)
        discovered = len(Nodes().nodes_discovered)

        Tabs().nodes.click()
        for i in range(discovered):
            Nodes().add_nodes.click()
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
        BaseTestCase.setUpClass()
        BaseTestCase.get_home()
        preconditions.Environment().simple_flat()
        Environments().create_cluster_boxes[0].click()

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
        BaseTestCase.setUp(self)
        Environments().create_cluster_boxes[0].click()

    def _test_group_by(self, group_by, nodes_in_groups):
        with Nodes() as n:
            n.group_by.select_by_visible_text(group_by)
            time.sleep(1)
            self.assertEqual(len(nodes_in_groups), len(n.node_groups), 'Groups amount')
            for i, group in enumerate(n.node_groups):
                self.assertEqual(
                    nodes_in_groups[i], len(group.nodes),
                    'Group #{0} has {1} nodes'.format(i, nodes_in_groups[i]))

    def test_group_by_roles(self):
        self._test_group_by('Roles', [1, 5])

    def test_group_by_hardware_info(self):
        self._test_group_by('Hardware Info', [1, 1, 2, 1, 1])

    def test_group_by_roles_and_hardware_info(self):
        self._test_group_by('Roles and hardware info', [1, 2, 1, 1, 1])