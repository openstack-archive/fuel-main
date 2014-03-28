import time
from pageobjects.base import PageObject
from pageobjects.environments import Environments, Wizard
from pageobjects.header import Header
from pageobjects.releases import Releases
from settings import OPENSTACK_RELEASE_CENTOS
from settings import OPENSTACK_RELEASE_UBUNTU, OPENSTACK_RELEASE_REDHAT
from settings import OPENSTACK_REDHAT, REDHAT_USERNAME, REDHAT_PASSWORD
from settings import REDHAT_SATELLITE, REDHAT_ACTIVATION_KEY
from tests.base import BaseTestCase
from nose.plugins.attrib import attr


class TestEnvWizard(BaseTestCase):

    def setUp(self):
        """Each test precondition

        Steps:
            1. Click on create environment
        """
        BaseTestCase.setUp(self)
        Environments().create_cluster_box.click()

    def test_name_field(self):
        """Test environment name

        Scenario:
            1. Enter Environment name
            2. Click next and then previous button
            3. Verify that correct name is displayed
            4. Clear environment name and click next
            5. Verify that message 'Environment name cannot be empty' appears
        """
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
        """Test existing environment name

        Scenario:
            1. Create environment with 'test name'
            2. Click create environment again
            3. Enter 'test name'
            4. Click next button
            5. Verify that message 'Environment with name test name
               already exists' appears
        """
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
        """Test environment release field

        Scenario:
            1. Enter environment name
            2. Select Havana on Ubuntu in release list
            3. Click next button
            4. Click previous button
            5. Verify that correct release is selected
        """
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            w.prev.click()
            self.assertEqual(w.release.first_selected_option.text,
                             OPENSTACK_RELEASE_UBUNTU)

    @attr('redhat')
    def test_rhel_empty_form(self):
        """Test validation of empty RHEL form

        Scenario:
            1. Enter environment name
            2. Select RHOS for RHEL in release list
            3. Click next button
            4. Verify that 'Invalid username' and 'Invalid password'
               messages appear
            5. Select RHN Satellite license and click next
            6. Verify that error messages appear
        """
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

    @attr('redhat')
    def test_rhel_form(self):
        """Test RHEL form on presence of necessary fields

        Scenario:
            1. Enter environment name
            2. Select RHOS for RHEL in release list
            3. Verify all necessary fields exist
            4. Select RHN Satellite license
            5. Verify satellite and activation key fields appear
            6. Select RHSM radio button
            7. Verify satellite and activation key fields disappear
        """
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
        """Test development mode

        Scenario:
            1. Enter environment name
            2. Select Havana on Ubuntu in release list and click next
            3. Select HA mode and click next
            4. Click previous
            5. Verify HA mode is selected
        """
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            w.mode_ha_compact.click()
            w.next.click()
            w.prev.click()
            self.assertTrue(w.mode_ha_compact.
                            find_element_by_tag_name('input').is_selected())
            self.assertFalse(w.mode_multinode.
                             find_element_by_tag_name('input').is_selected())

    def test_hypervisor_radios(self):
        """Select environment hypervisor

        Scenario:
            1. Enter environment name
            2. Select Havana on Ubuntu in release list and click next
            3. Click next again
            4. Select KVM hypervisor and click next
            5. Click previous
            6. Verify KVM is selected
        """
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            w.next.click()
            w.hypervisor_qemu.click()
            w.next.click()
            w.prev.click()
            self.assertTrue(w.hypervisor_qemu.
                            find_element_by_tag_name('input').is_selected())
            self.assertFalse(w.hypervisor_kvm.
                             find_element_by_tag_name('input').is_selected())

    def test_network_radios(self):
        """Select environment network

        Scenario:
            1. Enter environment name
            2. Select Havana on Ubuntu in release list
               and click next three times
            3. Select Neutron with GRE segmentation
            4. Click next and click previous button
            5. Verify Neutron with GRE network is selected
        """
        with Wizard() as w:
            w.name.send_keys(OPENSTACK_RELEASE_UBUNTU)
            w.release.select_by_visible_text(OPENSTACK_RELEASE_UBUNTU)
            w.next.click()
            w.next.click()
            w.next.click()
            w.network_neutron_gre.click()
            w.next.click()
            w.prev.click()
            self.assertFalse(w.network_nova.
                             find_element_by_tag_name('input').is_selected())
            self.assertTrue(w.network_neutron_gre.
                            find_element_by_tag_name('input').is_selected())
            self.assertFalse(w.network_neutron_vlan.
                             find_element_by_tag_name('input').is_selected())
            w.network_neutron_vlan.click()
            self.assertFalse(w.network_nova.
                             find_element_by_tag_name('input').is_selected())
            self.assertFalse(w.network_neutron_gre.
                             find_element_by_tag_name('input').is_selected())
            self.assertTrue(w.network_neutron_vlan.
                            find_element_by_tag_name('input').is_selected())

    def test_storage_radios(self):
        """Select environment storage

        Scenario:
            1. Enter environment name
            2. Select Havana on Ubuntu in release list
               and click next four times
            3. Select Ceph for Cinder and Glance
            4. Click next and click previous button
            5. Verify Ceph options are selected
        """
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
            self.assertFalse(w.storage_cinder_default.
                             find_element_by_tag_name('input').is_selected())
            self.assertTrue(w.storage_cinder_ceph.
                            find_element_by_tag_name('input').is_selected())
            self.assertFalse(w.storage_glance_default.
                             find_element_by_tag_name('input').is_selected())
            self.assertTrue(w.storage_glance_ceph.
                            find_element_by_tag_name('input').is_selected())

    def test_services_checkboxes(self):
        """Select environment additional services

        Scenario:
            1. Enter environment name
            2. Select Havana on Ubuntu in release list and
               click next three times
            3. Select Neutron with GRE network
            4. Click next two times
            5. Select install Savanna, Murano, Ceilometer
            6. Click next and previous button
            7. Verify checkboxes are selected
        """
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
            self.assertTrue(w.install_savanna.
                            find_element_by_tag_name('input').is_selected())
            self.assertTrue(w.install_murano.
                            find_element_by_tag_name('input').is_selected())
            self.assertTrue(w.install_ceilometer.
                            find_element_by_tag_name('input').is_selected())

    def test_cancel_button(self):
        """Cancel environment wizard

        Scenario:
            1. Enter environment name
            2. Select Havana on Ubuntu in release list and click next
            3. Select HA mode and click next
            4. Select KVM hypervisor and click next
            5. Select Neutron with GRE and click next
            6. Select Ceph options for Cinder and Glance and click next
            7. Select install Savanna, Murano and click next
            8. Click cancel button
            9. Click create environment again and check that
               all default values are selected
        """
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
            self.assertTrue(w.mode_multinode.
                            find_element_by_tag_name('input').is_selected())
            w.next.click()
            self.assertTrue(w.hypervisor_qemu.
                            find_element_by_tag_name('input').is_selected())
            w.next.click()
            self.assertTrue(w.network_nova.
                            find_element_by_tag_name('input').is_selected())
            w.next.click()
            self.assertTrue(w.storage_cinder_default.
                            find_element_by_tag_name('input').is_selected())
            self.assertTrue(w.storage_glance_default.
                            find_element_by_tag_name('input').is_selected())
            w.next.click()
            self.assertFalse(w.install_savanna.
                             find_element_by_tag_name('input').is_selected())
            self.assertFalse(w.install_murano.
                             find_element_by_tag_name('input').is_selected())


class TestEnvWizardRedHat(BaseTestCase):

    def setUp(self):
        """Each test precondition

        Steps:
            1. Click on create environment
        """
        BaseTestCase.clear_nailgun_database()
        BaseTestCase.setUp(self)
        Environments().create_cluster_box.click()

    @attr('redhat')
    def test_rhsm(self):
        """Download RHEL and RHOS by RHSM

        Scenario:
            1. Enter environment name
            2. Select RHOS in release list
            3. Enter Redhat username and password
            4. Click next till the end and click create
            5. Open releases tab
            6. Verify that RHOS status is active
        """
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

    @attr('redhat')
    def test_rhn_satellite(self):
        """Download RHEL and RHOS by RHN satellite

        Scenario:
            1. Enter environment name
            2. Select RHOS in release list
            3. Select RHN option
            4. Enter Redhat username and password, satellite
               hostname and activation key
            5. Click next till the end and click create
            6. Open releases tab
            7. Verify that RHOS status is active
        """
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
