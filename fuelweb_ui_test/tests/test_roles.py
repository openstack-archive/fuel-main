import time
from pageobjects.environments import Environments
from pageobjects.nodes import Nodes, RolesPanel
from tests import preconditions
from tests.base import BaseTestCase

ERROR_ROLE_CANNOT_COMBINE = 'This role cannot be combined ' \
                            'with the other roles already selected.'
ROLE_UNALLOCATED = 'UNALLOCATED'
ROLE_CONTROLLER = 'CONTROLLER'
ROLE_COMPUTE = 'COMPUTE'
ROLE_CINDER = 'CINDER'
ROLE_CEPH = 'CEPH-OSD'


class BaseClass(BaseTestCase):

    def assertNodeInRoles(self, node, roles):
        for role in roles:
            self.assertIn(role, node.roles.text, "node's roles")

    def setUp(self):
        BaseTestCase.setUp(self)
        Environments().create_cluster_boxes[0].click()
        Nodes().add_nodes.click()
        time.sleep(1)


class TestRolesSimpleFlat(BaseClass):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()
        preconditions.Environment.simple_flat()

    def test_controller(self):
        with Nodes()as n:
            n.nodes_discovered[0].checkbox.click()
        with RolesPanel() as r:
            r.controller.click()
            self.assertFalse(r.compute.is_enabled())
            self.assertIn(
                ERROR_ROLE_CANNOT_COMBINE,
                r.compute.find_element_by_xpath('../..').text,
                'error "{}" is visible'.format(ERROR_ROLE_CANNOT_COMBINE))
        with Nodes()as n:
            self.assertNodeInRoles(n.nodes_discovered[0], [ROLE_CONTROLLER])
            self.assertTrue(n.apply_changes.is_enabled())
            n.nodes_discovered[0].checkbox.click()
            self.assertFalse(n.apply_changes.is_enabled())
            self.assertNodeInRoles(n.nodes_discovered[0], [ROLE_UNALLOCATED])

    def test_one_controller_allowed_nodes_disabled(self):
        with Nodes()as n:
            n.nodes_discovered[0].checkbox.click()
        with RolesPanel() as r:
            r.controller.click()
        for n in Nodes().nodes_discovered[1:]:
            self.assertFalse(
                n.checkbox.find_element_by_tag_name('input').is_enabled(),
                'Checkbox is disabled')

    def test_one_controller_allowed_controller_role_disabled(self):
        with Nodes()as n:
            with RolesPanel() as r:
                n.nodes_discovered[0].checkbox.click()
                self.assertTrue(r.controller.is_enabled())
                for node in n.nodes_discovered[1:]:
                    node.checkbox.click()
                    self.assertFalse(r.controller.is_enabled())

    def test_compute(self):
        with Nodes()as n:
            n.nodes_discovered[0].checkbox.click()
        with RolesPanel() as r:
            r.compute.click()
            self.assertFalse(r.controller.is_enabled())
            self.assertIn(
                ERROR_ROLE_CANNOT_COMBINE,
                r.controller.find_element_by_xpath('../..').text,
                'error "{}" is visible'.format(ERROR_ROLE_CANNOT_COMBINE))
        with Nodes()as n:
            self.assertNodeInRoles(n.nodes_discovered[0], [ROLE_COMPUTE])
            self.assertTrue(n.apply_changes.is_enabled())
            n.nodes_discovered[0].checkbox.click()
            self.assertFalse(n.apply_changes.is_enabled())
            self.assertNodeInRoles(n.nodes_discovered[0], [ROLE_UNALLOCATED])

    def test_cinder(self):
        with Nodes()as n:
            n.nodes_discovered[0].checkbox.click()
        with RolesPanel() as r:
            r.cinder.click()
        with Nodes()as n:
            self.assertNodeInRoles(n.nodes_discovered[0], [ROLE_CINDER])
            self.assertTrue(n.apply_changes.is_enabled())
            n.nodes_discovered[0].checkbox.click()
            self.assertFalse(n.apply_changes.is_enabled())
            self.assertNodeInRoles(n.nodes_discovered[0], [ROLE_UNALLOCATED])

    def test_ceph(self):
        with Nodes()as n:
            n.nodes_discovered[0].checkbox.click()
        with RolesPanel() as r:
            r.ceph_osd.click()
        with Nodes()as n:
            self.assertNodeInRoles(n.nodes_discovered[0], [ROLE_CEPH])
            self.assertTrue(n.apply_changes.is_enabled())
            n.nodes_discovered[0].checkbox.click()
            self.assertFalse(n.apply_changes.is_enabled())
            self.assertNodeInRoles(n.nodes_discovered[0], [ROLE_UNALLOCATED])

    def test_multiroles(self):
        with Nodes()as n:
            n.nodes_discovered[0].checkbox.click()
        with RolesPanel() as r:
            r.controller.click()
            r.cinder.click()
            r.ceph_osd.click()
        with Nodes()as n:
            self.assertNodeInRoles(
                n.nodes_discovered[0],
                [ROLE_CONTROLLER, ROLE_CINDER, ROLE_CEPH])

    def test_several_nodes(self):
        with Nodes()as n:
            n.nodes_discovered[0].checkbox.click()
            n.nodes_discovered[1].checkbox.click()
            n.nodes_discovered[2].checkbox.click()
        with RolesPanel() as r:
            r.compute.click()
            r.cinder.click()
            r.ceph_osd.click()
        with Nodes()as n:
            self.assertNodeInRoles(
                n.nodes_discovered[0],
                [ROLE_COMPUTE, ROLE_CINDER, ROLE_CEPH])
            self.assertNodeInRoles(
                n.nodes_discovered[1],
                [ROLE_COMPUTE, ROLE_CINDER, ROLE_CEPH])
            self.assertNodeInRoles(
                n.nodes_discovered[2],
                [ROLE_COMPUTE, ROLE_CINDER, ROLE_CEPH])


class TestRolesHAFlat(BaseClass):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()
        preconditions.Environment.ha_flat()

    def test_controller_role_always_enabled(self):
        with Nodes()as n:
            for node in n.nodes_discovered:
                node.checkbox.click()
                self.assertTrue(RolesPanel().controller.is_enabled())
            RolesPanel().controller.click()
            for node in n.nodes_discovered:
                self.assertNodeInRoles(node, [ROLE_CONTROLLER])

    def test_all_nodes_could_be_controller(self):
        RolesPanel().controller.click()
        with Nodes()as n:
            for node in n.nodes_discovered:
                node.checkbox.click()
            for node in n.nodes_discovered:
                self.assertNodeInRoles(node, [ROLE_CONTROLLER])
