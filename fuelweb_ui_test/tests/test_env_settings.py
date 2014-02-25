import time
import random
from pageobjects.environments import Environments, Wizard
from pageobjects.settings import Settings
from pageobjects.tabs import Tabs
from settings import OPENSTACK_CENTOS, OPENSTACK_RELEASE_CENTOS
from tests.base import BaseTestCase


class BaseClass(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        """Global precondition

        Steps:
            1. Create simple environment with Neutron with GRE segmentation
        """
        BaseTestCase.setUpClass()
        cls.get_home()
        Environments().create_cluster_box.click()
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

    def setUp(self):
        """Each test precondition

        Steps:
            1. Click on created environment
            2. Open Settings tab
        """
        BaseTestCase.setUp(self)
        Environments().create_cluster_boxes[0].click()
        Tabs().settings.click()

    def _test_text_field(self, text_field, value):
        def_value = None
        with Settings() as s:
            def_value = getattr(s, text_field).get_attribute('value')
            getattr(s, text_field).clear()
            getattr(s, text_field).send_keys(value)
            s.save_settings.click()
            time.sleep(1)
        self.refresh()
        with Settings() as s:
            self.assertEqual(getattr(s, text_field).get_attribute('value'),
                             value)
            s.load_defaults.click()
            time.sleep(1)
            self.assertEqual(
                getattr(s, text_field).get_attribute('value'), def_value,
                "load defaults value")

    def _test_tumbler_field(self, tumbler_field):
        def_value = None
        with Settings() as s:
            def_value = getattr(s, tumbler_field).\
                find_element_by_tag_name('input').is_selected()
            getattr(s, tumbler_field).click()
            s.save_settings.click()
            time.sleep(1)
        self.refresh()
        with Settings() as s:
            self.assertEqual(
                getattr(s, tumbler_field).
                find_element_by_tag_name('input').is_selected(), not def_value)
            s.load_defaults.click()
            time.sleep(1)
            self.assertEqual(
                getattr(s, tumbler_field).
                find_element_by_tag_name('input').is_selected(), def_value,
                "load defaults value")

    def _test_radio_group(self, radios):
        radios.reverse()
        for radio in radios:
            with Settings() as s:
                getattr(s, radio).click()
                s.save_settings.click()
                time.sleep(1)
                self.refresh()
            self.assertTrue(
                getattr(Settings(), radio).
                find_element_by_tag_name('input').is_selected())
        # Set group to not default state
        random_radio = radios[random.randint(0, len(radios) - 2)]
        with Settings() as s:
            getattr(s, random_radio).click()
            s.load_defaults.click()
            time.sleep(1)
            self.assertTrue(
                getattr(s, radios[-1]).
                find_element_by_tag_name('input').is_selected(),
                "load defaults value")


class TestAccess(BaseClass):

    def test_username(self):
        """Change username

        Scenario:
            1. Enter new username
            2. Save settings
            3. Verify that username is correctly saved
            4. Click Load defaults
            5. Verify that previous username is displayed
        """
        self._test_text_field('username', 'newname')

    def test_password(self):
        """Change password

        Scenario:
            1. Enter new password
            2. Save settings
            3. Verify that password is correctly saved
            4. Click Load defaults
            5. Verify that previous password is activated
        """
        self._test_text_field('password', 'newpassword')

    def test_password_show(self):
        """Show password feature

        Scenario:
            1. Click show password button
            2. Verify that text of the password is displayed
            3. Click on show password button again
            4. Verify that password text isn't displayed
        """
        with Settings() as s:
            s.show_password.click()
            self.assertEqual(s.password.get_attribute('type'), 'text')
            s.show_password.click()
            self.assertEqual(s.password.get_attribute('type'), 'password')

    def test_tenant(self):
        """Change tenant

        Scenario:
            1. Enter new tenant
            2. Save settings
            3. Verify that tenant is correctly saved
            4. Click Load defaults
            5. Verify that previous tenant name is displayed
        """
        self._test_text_field('tenant', 'newtenant')

    def test_email(self):
        """Change email

        Scenario:
            1. Enter new email
            2. Save settings
            3. Verify that email is correctly saved
            4. Click Load defaults
            5. Verify that previous email is displayed
        """
        self._test_text_field('email', 'newemail@example.org')


class TestAdditionalComponents(BaseClass):

    def test_savanna(self):
        """Install Savanna component

        Scenario:
            1. Click on Install Savanna checkbox
            2. Save settings
            3. Verify that Install Savanna checkbox is selected
            4. Click Load defaults
            5. Verify that Install Savanna checkbox is not selected
        """
        self._test_tumbler_field('install_savanna')

    def test_murano(self):
        """Install Murano component

        Scenario:
            1. Click on Install Murano checkbox
            2. Save settings
            3. Verify that Install Murano checkbox is selected
            4. Click Load defaults
            5. Verify that Install Murano checkbox is not selected
        """
        self._test_tumbler_field('install_murano')

    def test_ceilometer(self):
        """Install Ceilometer component

        Scenario:
            1. Click on Install Ceilometer checkbox
            2. Save settings
            3. Verify that Install Ceilometer checkbox is selected
            4. Click Load defaults
            5. Verify that Install Ceilometer checkbox is not selected
        """
        self._test_tumbler_field('install_ceilometer')


class TestCommon(BaseClass):

    def test_debug(self):
        """Enable OpenStack debug logging

        Scenario:
            1. Click on OpenStack debug logging checkbox
            2. Save settings
            3. Verify that OpenStack debug logging checkbox is selected
            4. Click Load defaults
            5. Verify that OpenStack debug logging checkbox is not selected
        """
        self._test_tumbler_field('debug')

    def test_hypervisor_type(self):
        """Change hypervisor type

        Scenario:
            1. Select hypervisor type 'KVM'
            2. Save settings
            3. Verify that KVM hypervisor type is selected
            4. Click Load defaults
            5. Verify that QEMU hypervisor is selected
        """
        self._test_radio_group(['hypervisor_qemu', 'hypervisor_kvm'])

    def test_assign_ip(self):
        """Enable Auto assign floating IP

        Scenario:
            1. Click on Auto assign floating IP checkbox
            2. Save settings
            3. Verify that Auto assign floating IP checkbox is selected
            4. Click Load defaults
            5. Verify that Auto assign floating IP checkbox is not selected
        """
        self._test_tumbler_field('assign_ip')

    def test_scheduler_driver(self):
        """Change scheduler driver

        Scenario:
            1. Select 'Simple scheduler' radio button
            2. Save settings
            3. Verify that 'Simple scheduler' is selected
            4. Click Load defaults
            5. Verify that 'Filter scheduler' is selected
        """
        self._test_radio_group(['filter_scheduler', 'simple_scheduler'])

    def test_vlan_splinters(self):
        """Enable VSwitch VLAN splinters

        Scenario:
            1. Select 'OVS VLAN splinters soft trunks' radio button
            2. Save settings
            3. Verify that 'OVS VLAN splinters soft trunks' is selected
            4. Click Load defaults
            5. Verify that 'Disabled' is selected
        """
        self._test_radio_group(
            ['vlan_splinters_disabled', 'vlan_splinters_soft',
             'vlan_splinters_hard'])

    def test_use_cow_images(self):
        """Enable 'Use qcow format for images'

        Scenario:
            1. Click on 'Use qcow format for images' checkbox
            2. Save settings
            3. Verify that 'Use qcow format for images' checkbox is selected
            4. Click Load defaults
            5. Verify that 'Use qcow format for images'
               checkbox is not selected
        """
        self._test_tumbler_field('use_cow_images')

    def test_start_guests(self):
        """Enable 'Start guests on host boot'

        Scenario:
            1. Click on 'Start guests on host boot' checkbox
            2. Save settings
            3. Verify that 'Start guests on host boot' checkbox is selected
            4. Click Load defaults
            5. Verify that 'Start guests on host boot' checkbox is not selected
        """
        self._test_tumbler_field('start_guests')

    def test_auth_key(self):
        """Change authorization key

        Scenario:
            1. Enter new authorization key
            2. Save settings
            3. Verify that authorization key is correctly saved
            4. Click Load defaults
            5. Verify that default authorization key is active
        """
        self._test_text_field('auth_key', 'newauthkey')


class TestSyslog(BaseClass):

    def test_hostname(self):
        """Change hostname

        Scenario:
            1. Enter new hostname
            2. Save settings
            3. Verify that hostname is correctly saved
            4. Click Load defaults
            5. Verify that default hostname is displayed
        """
        self._test_text_field('syslog_server', 'newsyslog_server')

    def test_port(self):
        """Change port

        Scenario:
            1. Enter new port value
            2. Save settings
            3. Verify that port value is correctly saved
            4. Click Load defaults
            5. Verify that default port value is displayed
        """
        self._test_text_field('syslog_port', '8000')

    def test_syslog_protocol(self):
        """Change syslog transport protocol

        Scenario:
            1. Select 'TCP' radio button
            2. Save settings
            3. Verify that 'TCP' is selected
            4. Click Load defaults
            5. Verify that 'UDP' is selected
        """
        self._test_radio_group(['syslog_udp', 'syslog_tcp'])


class TestStorage(BaseClass):

    def test_cinder_for_volumes(self):
        """Enable 'Cinder LVM'

        Scenario:
            1. Click on 'Cinder LVM' checkbox
            2. Save settings
            3. Verify that 'Cinder LVM' checkbox is not selected
            4. Click Load defaults
            5. Verify that 'Cinder LVM' checkbox is selected
        """
        self._test_tumbler_field('cinder_for_volumes')

    def test_ceph_for_volumes(self):
        """Enable 'Ceph for volumes'

        Scenario:
            1. Click on 'Ceph for volumes' checkbox
            2. Save settings
            3. Verify that 'Ceph for volumes' checkbox is selected
            4. Click Load defaults
            5. Verify that 'Ceph for volumes' checkbox is not selected
        """
        self._test_tumbler_field('ceph_for_volumes')

    def test_ceph_for_images(self):
        """Enable 'Ceph for images'

        Scenario:
            1. Click on 'Ceph for images' checkbox
            2. Save settings
            3. Verify that 'Ceph for images' checkbox is selected
            4. Click Load defaults
            5. Verify that 'Ceph for images' checkbox is not selected
        """
        self._test_tumbler_field('ceph_for_images')

    def test_ceph_ephemeral(self):
        """Enable 'Ceph for ephemeral'

        Scenario:
            1. Click on 'Ceph for ephemeral' checkbox
            2. Save settings
            3. Verify that 'Ceph for ephemeral' checkbox is selected
            4. Click Load defaults
            5. Verify that 'Ceph for ephemeral' checkbox is not selected
        """
        self._test_tumbler_field('ceph_ephemeral')

    def test_ceph_rados_gw(self):
        """Enable 'Ceph RadosGW for objects'

        Scenario:
            1. Click on 'Ceph RadosGW for objects' checkbox
            2. Save settings
            3. Verify that 'Ceph RadosGW for objects' checkbox is selected
            4. Click Load defaults
            5. Verify that 'Ceph RadosGW for objects' checkbox is not selected
        """
        self._test_tumbler_field('ceph_rados_gw')

    def test_ceph_factor(self):
        """Change ceph factor

        Scenario:
            1. Enter new ceph factor
            2. Save settings
            3. Verify that ceph factor value is correctly saved
            4. Click Load defaults
            5. Verify that default ceph factor value is displayed
        """
        self._test_text_field('ceph_factor', '10')
