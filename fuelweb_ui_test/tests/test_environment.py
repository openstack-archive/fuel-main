from pageobjects.environments import Environments, Wizard
from pageobjects.networks import Networks, NeutronParameters
from pageobjects.nodes import Nodes
from pageobjects.settings import Settings
from pageobjects.tabs import Tabs
from tests.base import BaseTestCase
from fuelweb_ui_test.settings import OPENSTACK_CENTOS
from fuelweb_ui_test.settings import OPENSTACK_RELEASE_CENTOS


class TestEnvironment(BaseTestCase):

    def setUp(self):
        self.clear_nailgun_database()
        BaseTestCase.setUp(self)
        Environments().create_cluster_box.click()

    def test_default_settings(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_CENTOS)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_CENTOS)
            for i in range(6):
                w.next.click()
            w.create.click()
            w.wait_until_exists()

        cb = Environments().create_cluster_boxes[0]
        self.assertIn(OPENSTACK_CENTOS, cb.text)
        cb.click()

        with Nodes() as n:
            self.assertEqual(n.env_name.text, OPENSTACK_CENTOS)
            n.info_icon.click()
            self.assertIn('display: block;',
                          n.env_details.get_attribute('style'))
            self.assertIn(OPENSTACK_CENTOS, n.env_details.text)
            self.assertIn('New', n.env_details.text)
            self.assertIn('Multi-node', n.env_details.text)
            self.assertNotIn('with HA', n.env_details.text)
            n.info_icon.click()
            self.assertIn('display: none;',
                          n.env_details.get_attribute('style'))
        Tabs().networks.click()
        with Networks() as n:
            self.assertTrue(
                n.flatdhcp_manager.find_element_by_tag_name('input').
                is_selected())
        Tabs().settings.click()
        with Settings() as s:
            self.assertFalse(
                s.install_savanna.find_element_by_tag_name('input').
                is_selected())
            self.assertFalse(
                s.install_murano.find_element_by_tag_name('input').
                is_selected())
            self.assertFalse(
                s.install_ceilometer.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                s.hypervisor_qemu.find_element_by_tag_name('input').
                is_selected())
        pass

    def test_ha_mode(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_CENTOS)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_CENTOS)
            w.next.click()
            w.mode_ha_compact.click()
            for i in range(5):
                w.next.click()
            w.create.click()
            w.wait_until_exists()

        cb = Environments().create_cluster_boxes[0]
        cb.click()

        with Nodes() as n:
            self.assertEqual(n.env_name.text, OPENSTACK_CENTOS)
            n.info_icon.click()
            self.assertIn(OPENSTACK_CENTOS, n.env_details.text)
            self.assertIn('Multi-node with HA', n.env_details.text)

    def test_hypervisor_kvm(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_CENTOS)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_CENTOS)
            w.next.click()
            w.next.click()
            w.hypervisor_kvm.click()
            for i in range(4):
                w.next.click()
            w.create.click()
            w.wait_until_exists()

        cb = Environments().create_cluster_boxes[0]
        cb.click()
        Tabs().settings.click()

        with Settings() as s:
            self.assertTrue(
                s.hypervisor_kvm.find_element_by_tag_name('input').
                is_selected())

    def test_neutron_gre(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_CENTOS)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_CENTOS)
            for i in range(3):
                w.next.click()
            w.network_neutron_gre.click()
            for i in range(3):
                w.next.click()
            w.create.click()
            w.wait_until_exists()

        cb = Environments().create_cluster_boxes[0]
        cb.click()
        Tabs().networks.click()

        with Networks() as n:
            self.assertEqual(n.segmentation_type.text,
                             'Neutron with gre segmentation')
            self.assertTrue(NeutronParameters().parent.is_displayed())

    def test_neutron_vlan(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_CENTOS)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_CENTOS)
            for i in range(3):
                w.next.click()
            w.network_neutron_vlan.click()
            for i in range(3):
                w.next.click()
            w.create.click()
            w.wait_until_exists()

        cb = Environments().create_cluster_boxes[0]
        cb.click()
        Tabs().networks.click()

        with Networks() as n:
            self.assertEqual(n.segmentation_type.text,
                             'Neutron with vlan segmentation')
            self.assertTrue(NeutronParameters().parent.is_displayed())

    def test_storage_ceph(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_CENTOS)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_CENTOS)
            for i in range(4):
                w.next.click()
            w.storage_cinder_ceph.click()
            w.storage_glance_ceph.click()
            w.next.click()
            w.next.click()
            w.create.click()
            w.wait_until_exists()

        cb = Environments().create_cluster_boxes[0]
        cb.click()
        Tabs().settings.click()

        with Settings() as s:
            self.assertTrue(
                s.cinder_for_volumes.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                s.ceph_for_volumes.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                s.ceph_for_images.find_element_by_tag_name('input').
                is_selected())
            self.assertFalse(
                s.ceph_rados_gw.find_element_by_tag_name('input').
                is_selected())

    def test_services(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_CENTOS)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_CENTOS)
            for i in range(3):
                w.next.click()
            w.network_neutron_gre.click()
            w.next.click()
            w.next.click()
            w.install_savanna.click()
            w.install_murano.click()
            w.install_ceilometer.click()
            w.next.click()
            w.create.click()
            w.wait_until_exists()

        cb = Environments().create_cluster_boxes[0]
        cb.click()
        Tabs().settings.click()

        with Settings() as s:
            self.assertTrue(
                s.install_savanna.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                s.install_murano.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                s.install_ceilometer.find_element_by_tag_name('input').
                is_selected())
