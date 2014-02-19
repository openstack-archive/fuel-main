from pageobjects.base import PageObject
from pageobjects.environments import RedhatAccountPopup
from pageobjects.header import Header
from pageobjects.releases import Releases
from fuelweb_ui_test.settings import OPENSTACK_REDHAT
from fuelweb_ui_test.settings import REDHAT_USERNAME
from fuelweb_ui_test.settings import REDHAT_PASSWORD
from fuelweb_ui_test.settings import REDHAT_SATELLITE
from fuelweb_ui_test.settings import REDHAT_ACTIVATION_KEY
from fuelweb_ui_test.settings import OPENSTACK_CENTOS
from fuelweb_ui_test.settings import OPENSTACK_UBUNTU
from tests.base import BaseTestCase


class TestReleases(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()

    def setUp(self):
        BaseTestCase.clear_nailgun_database()
        BaseTestCase.setUp(self)
        Header().releases.click()

    def test_centos_is_active(self):
        with Releases() as r:
            self.assertEqual(
                'Active', r.dict[OPENSTACK_CENTOS].status.text,
                'CentOS status is active')

    def test_ubuntu_is_active(self):
        with Releases() as r:
            self.assertEqual(
                'Active', r.dict[OPENSTACK_UBUNTU].status.text,
                'Ubuntu status is active')

    def test_rhos_is_active(self):
        with Releases() as r:
            self.assertEqual(
                'Not available', r.dict[OPENSTACK_REDHAT].status.text,
                'RHOS status is Not available')

    def test_rhsm(self):
        Releases().rhel_setup.click()
        with RedhatAccountPopup() as p:
            p.license_rhsm.click()
            p.redhat_username.send_keys(REDHAT_USERNAME)
            p.redhat_password.send_keys(REDHAT_PASSWORD)
            p.apply.click()
            p.wait_until_exists()
        with Releases() as r:
            PageObject.wait_until_exists(
                r.dict[OPENSTACK_REDHAT].download_progress, timeout=20)
            self.assertEqual(
                'Active', r.dict[OPENSTACK_REDHAT].status.text,
                'RHOS status is active')

    def test_rhn_satellite(self):
        Releases().rhel_setup.click()
        with RedhatAccountPopup() as p:
            p.license_rhn.click()
            p.redhat_username.send_keys(REDHAT_USERNAME)
            p.redhat_password.send_keys(REDHAT_PASSWORD)
            p.redhat_satellite.send_keys(REDHAT_SATELLITE)
            p.redhat_activation_key.send_keys(REDHAT_ACTIVATION_KEY)
            p.apply.click()
            p.wait_until_exists()
        with Releases() as r:
            PageObject.wait_until_exists(
                r.dict[OPENSTACK_REDHAT].download_progress, timeout=20)
            self.assertEqual(
                'Active', r.dict[OPENSTACK_REDHAT].status.text,
                'RHOS status is active')
