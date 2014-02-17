import time
import random
from pageobjects.environments import Environments, Wizard
from pageobjects.settings import Settings
from pageobjects.tabs import Tabs
from settings import *
from tests.base import BaseTestCase


class BaseClass(BaseTestCase):

    @classmethod
    def setUpClass(cls):
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
            self.assertEqual(getattr(s, text_field).get_attribute('value'), value)
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
        self._test_text_field('username', 'newname')

    def test_password(self):
        self._test_text_field('password', 'newpassword')

    def test_password_show(self):
        with Settings() as s:
            s.show_password.click()
            self.assertEqual(s.password.get_attribute('type'), 'text')
            s.show_password.click()
            self.assertEqual(s.password.get_attribute('type'), 'password')

    def test_tenant(self):
        self._test_text_field('tenant', 'newtenant')

    def test_email(self):
        self._test_text_field('email', 'newemail@example.org')


class TestAdditionalComponents(BaseClass):

    def test_savanna(self):
        self._test_tumbler_field('install_savanna')

    def test_murano(self):
        self._test_tumbler_field('install_murano')

    def test_ceilometer(self):
        self._test_tumbler_field('install_ceilometer')


class TestCommon(BaseClass):

    def test_debug(self):
        self._test_tumbler_field('debug')

    def test_hypervisor_type(self):
        self._test_radio_group(['hypervisor_qemu', 'hypervisor_kvm'])

    def test_assign_ip(self):
        self._test_tumbler_field('assign_ip')

    def test_scheduler_driver(self):
        self._test_radio_group(['filter_scheduler', 'simple_scheduler'])

    def test_vlan_splinters(self):
        self._test_radio_group(
            ['vlan_splinters_disabled', 'vlan_splinters_soft', 'vlan_splinters_hard'])

    def test_use_cow_images(self):
        self._test_tumbler_field('use_cow_images')

    def test_start_guests(self):
        self._test_tumbler_field('start_guests')

    def test_auth_key(self):
        self._test_text_field('auth_key', 'newauthkey')


class TestSyslog(BaseClass):

    def test_hostname(self):
        self._test_text_field('syslog_server', 'newsyslog_server')

    def test_port(self):
        self._test_text_field('syslog_port', '8000')

    def test_syslog_protocol(self):
        self._test_radio_group(['syslog_udp', 'syslog_tcp'])


class TestStorage(BaseClass):

    def test_cinder_for_volumes(self):
        self._test_tumbler_field('cinder_for_volumes')

    def test_ceph_for_volumes(self):
        self._test_tumbler_field('ceph_for_volumes')

    def test_ceph_for_images(self):
        self._test_tumbler_field('ceph_for_images')

    def test_ceph_ephemeral(self):
        self._test_tumbler_field('ceph_ephemeral')

    def test_ceph_rados_gw(self):
        self._test_tumbler_field('ceph_rados_gw')

    def test_ceph_factor(self):
        self._test_text_field('ceph_factor', '10')