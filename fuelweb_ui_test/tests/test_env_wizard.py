import time
from pageobjects.base import PageObject
from pageobjects.environments import Environments, Wizard
from pageobjects.header import Header
from pageobjects.releases import Releases
from tests.base import BaseTestCase
from fuelweb_ui_test.settings import OPENSTACK_RELEASE_CENTOS
from fuelweb_ui_test.settings import OPENSTACK_RELEASE_UBUNTU
from fuelweb_ui_test.settings import OPENSTACK_RELEASE_REDHAT
from fuelweb_ui_test.settings import REDHAT_USERNAME
from fuelweb_ui_test.settings import REDHAT_PASSWORD
from fuelweb_ui_test.settings import OPENSTACK_REDHAT
from fuelweb_ui_test.settings import REDHAT_SATELLITE
from fuelweb_ui_test.settings import REDHAT_ACTIVATION_KEY


class TestEnvWizard(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)
        Environments().create_cluster_box.click()

    def test_name_field(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_CENTOS)
            w.next.click()
            w.prev.click()
            self.assertEqual(w.name.get_attribute('value'),
                             OPENSTACK_RELEASE_CENTOS)
            w.name.clear()
            w.next.click()
            self.assertIn(
                'Environment name cannot be empty',
                w.name.find_element_by_xpath('..').text)

    def test_name_exists(self):
        name = 'test name'
        with Wizard() as w:
            w.name.send_keys(name)
            for i in range(6):
                w.next.click()
            w.create.click()
            w.wait_until_exists()

        Environments().create_cluster_box.click()
        with Wizard() as w:
            w.name.send_keys(name)
            w.next.click()
            time.sleep(1)
            self.assertIn('Environment with name "{}" already exists'.
                          format(name),
                          w.name.find_element_by_xpath('..').text)

    def test_release_field(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            w.prev.click()
            self.assertEqual(w.release.first_selected_option.text,
                             OPENSTACK_RELEASE_UBUNTU)

    def test_rhel_empty_form(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_REDHAT)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_REDHAT)
            w.next.click()
            self.assertIn('Invalid username',
                          w.redhat_username.find_element_by_xpath('..').text)
            self.assertIn('Invalid password',
                          w.redhat_password.find_element_by_xpath('..').text)

            w.license_rhn.click()
            w.next.click()
            self.assertIn('Invalid username',
                          w.redhat_username.find_element_by_xpath('..').text)
            self.assertIn('Invalid password',
                          w.redhat_password.find_element_by_xpath('..').text)
            self.assertIn(
                'Only valid fully qualified domain name is allowed for the '
                'hostname field',
                w.redhat_satellite.find_element_by_xpath('..').text)
            self.assertIn(
                'Invalid activation key',
                w.redhat_activation_key.find_element_by_xpath('..').text)

    def test_rhel_form(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_REDHAT)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_REDHAT)
            self.assertTrue(w.license_rhsm.is_displayed())
            self.assertTrue(w.license_rhn.is_displayed())
            self.assertTrue(w.redhat_username.is_displayed())
            self.assertTrue(w.redhat_password.is_displayed())

            w.license_rhn.click()
            self.assertTrue(w.redhat_satellite.is_displayed())
            self.assertTrue(w.redhat_activation_key.is_displayed())

            w.license_rhsm.click()
            self.assertFalse(w.redhat_satellite.is_displayed())
            self.assertFalse(w.redhat_activation_key.is_displayed())

    def test_mode_radios(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            w.mode_ha_compact.click()
            w.next.click()
            w.prev.click()
            self.assertTrue(
                w.mode_ha_compact.
                find_element_by_tag_name('input').is_selected())
            self.assertFalse(
                w.mode_multinode.
                find_element_by_tag_name('input').is_selected())

    def test_hypervisor_radios(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            w.next.click()
            w.hypervisor_qemu.click()
            w.next.click()
            w.prev.click()
            self.assertTrue(
                w.hypervisor_qemu.find_element_by_tag_name('input').
                is_selected())
            self.assertFalse(
                w.hypervisor_kvm.find_element_by_tag_name('input').
                is_selected())

    def test_network_radios(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            w.next.click()
            w.next.click()
            w.network_neutron_gre.click()
            w.next.click()
            w.prev.click()
            self.assertFalse(
                w.network_nova.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                w.network_neutron_gre.find_element_by_tag_name('input').
                is_selected())
            self.assertFalse(
                w.network_neutron_vlan.find_element_by_tag_name('input').
                is_selected())
            w.network_neutron_vlan.click()
            self.assertFalse(
                w.network_nova.find_element_by_tag_name('input').is_selected())
            self.assertFalse(
                w.network_neutron_gre.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                w.network_neutron_vlan.find_element_by_tag_name('input').
                is_selected())

    def test_storage_radios(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            w.next.click()
            w.next.click()
            w.next.click()
            w.storage_cinder_ceph.click()
            w.storage_glance_ceph.click()
            w.next.click()
            w.prev.click()
            self.assertFalse(
                w.storage_cinder_default.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                w.storage_cinder_ceph.find_element_by_tag_name('input').
                is_selected())
            self.assertFalse(
                w.storage_glance_default.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                w.storage_glance_ceph.find_element_by_tag_name('input').
                is_selected())

    def test_services_checkboxes(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            w.next.click()
            w.next.click()
            w.network_neutron_gre.click()
            w.next.click()
            w.next.click()
            w.install_savanna.click()
            w.install_murano.click()
            w.install_ceilometer.click()
            w.next.click()
            w.prev.click()
            self.assertTrue(
                w.install_savanna.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                w.install_murano.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                w.install_ceilometer.find_element_by_tag_name('input').
                is_selected())

    def test_cancel_button(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            w.mode_ha_compact.click()
            w.next.click()
            w.hypervisor_kvm.click()
            w.next.click()
            w.network_neutron_gre.click()
            w.next.click()
            w.storage_cinder_ceph.click()
            w.storage_glance_ceph.click()
            w.next.click()
            w.install_savanna.click()
            w.install_murano.click()
            w.next.click()
            w.cancel.click()
            PageObject.wait_until_exists(w.parent)

        Environments().create_cluster_box.click()
        with Wizard() as w:
            self.assertEqual(w.name.get_attribute('value'), '')
            self.assertEqual(w.release.first_selected_option.text,
                             OPENSTACK_RELEASE_CENTOS)
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            self.assertTrue(
                w.mode_multinode.find_element_by_tag_name('input').
                is_selected())
            w.next.click()
            self.assertTrue(
                w.hypervisor_qemu.find_element_by_tag_name('input').
                is_selected())
            w.next.click()
            self.assertTrue(
                w.network_nova.find_element_by_tag_name('input').
                is_selected())
            w.next.click()
            self.assertTrue(
                w.storage_cinder_default.find_element_by_tag_name('input').
                is_selected())
            self.assertTrue(
                w.storage_glance_default.find_element_by_tag_name('input').
                is_selected())
            w.next.click()
            self.assertFalse(
                w.install_savanna.find_element_by_tag_name('input').
                is_selected())
            self.assertFalse(
                w.install_murano.find_element_by_tag_name('input').
                is_selected())


class TestEnvWizardRedHat(BaseTestCase):

    def setUp(self):
        BaseTestCase.clear_nailgun_database()
        BaseTestCase.setUp(self)
        Environments().create_cluster_box.click()

    def test_rhsm(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_REDHAT)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_REDHAT)
            w.license_rhsm.click()
            w.redhat_username.send_keys(REDHAT_USERNAME)
            w.redhat_password.send_keys(REDHAT_PASSWORD)
            for i in range(6):
                w.next.click()
            w.create.click()
            w.wait_until_exists()
        Header().releases.click()
        with Releases() as r:
            PageObject.wait_until_exists(
                r.dict[OPENSTACK_REDHAT].download_progress, timeout=20)
            self.assertEqual(
                'Active', r.dict[OPENSTACK_REDHAT].status.text,
                'RHOS status is active')

    def test_rhn_satellite(self):
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_REDHAT)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_REDHAT)
            w.license_rhn.click()
            w.redhat_username.send_keys(REDHAT_USERNAME)
            w.redhat_password.send_keys(REDHAT_PASSWORD)
            w.redhat_satellite.send_keys(REDHAT_SATELLITE)
            w.redhat_activation_key.send_keys(REDHAT_ACTIVATION_KEY)
            for i in range(6):
                w.next.click()
            w.create.click()
            w.wait_until_exists()
        Header().releases.click()
        with Releases() as r:
            PageObject.wait_until_exists(
                r.dict[OPENSTACK_REDHAT].download_progress, timeout=20)
            self.assertEqual(
                'Active', r.dict[OPENSTACK_REDHAT].status.text,
                'RHOS status is active')
