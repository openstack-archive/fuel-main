from pageobjects.base import PageObject
from pageobjects.environments import RedhatAccountPopup
from pageobjects.header import Header
from pageobjects.releases import Releases
from settings import OPENSTACK_REDHAT, REDHAT_USERNAME, REDHAT_PASSWORD, \
    REDHAT_SATELLITE, REDHAT_ACTIVATION_KEY, OPENSTACK_CENTOS, \
    OPENSTACK_UBUNTU
from tests.base import BaseTestCase
from nose.plugins.attrib import attr


class TestReleases(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()

    def setUp(self):
        BaseTestCase.clear_nailgun_database()
        BaseTestCase.setUp(self)
        Header().releases.click()

    def test_centos_is_active(self):
        """Check Centos status is active on releases tab

        Scenario:
            1. Open releases tab
            2. Check that Centos status is active
        """
        with Releases() as r:
            self.assertEqual(
                'Active', r.dict[OPENSTACK_CENTOS].status.text,
                'CentOS status is active')

    def test_ubuntu_is_active(self):
        """Check Ubuntu status is active on releases tab

        Scenario:
            1. Open releases tab
            2. Check that Ubuntu status is active
        """
        with Releases() as r:
            self.assertEqual(
                'Active', r.dict[OPENSTACK_UBUNTU].status.text,
                'Ubuntu status is active')

    @attr('redhat')
    def test_rhos_is_active(self):
        """Check RHOS status is active on releases tab

        Scenario:
            1. Open releases tab
            2. Check that RHOS status is Not available
        """
        with Releases() as r:
            self.assertEqual(
                'Not available', r.dict[OPENSTACK_REDHAT].status.text,
                'RHOS status is Not available')

    @attr('redhat')
    def test_rhsm(self):
        """Download RHEL with RHSM option

        Scenario:
            1. Open releases tab
            2. Click Configure button in actions column
            3. Select 'RHSM' radiobutton
            4. Enter username and password and click apply
            5. Check that RHOS status is active
        """
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

    @attr('redhat')
    def test_rhn_satellite(self):
        """Download RHEL with RHN option

        Scenario:
            1. Open releases tab
            2. Click Configure button in actions column
            3. Select 'RHN' radiobutton
            4. Enter username and password
            5. Enter satellite hostname, activation key and click apply
            6. Check that RHOS status is active
        """
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
