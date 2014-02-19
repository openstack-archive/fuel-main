import re
import time
import browser
from pageobjects.base import PageObject
from pageobjects.header import Header
from pageobjects.support import Support
from tests.base import BaseTestCase


class TestSupport(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()

    def setUp(self):
        BaseTestCase.clear_nailgun_database()
        BaseTestCase.setUp(self)
        time.sleep(1)
        Header().support.click()
        time.sleep(1)

    def test_register_fuel(self):
        with Support() as s:
            key = re.search(
                'key=(?P<key>.*)',
                s.register_fuel.get_attribute('href')).group('key')
            self.assertEqual(216, len(key), 'Key not empty')

            s.register_fuel.click()
            time.sleep(4)
        browser.driver.switch_to_window(browser.driver.window_handles.pop())
        self.assertTrue(
            browser.driver.find_element_by_css_selector(
                '[value="Register and Activate subscription"]').is_displayed(),
            '"Register and Activate subscription" is displayed')

    def test_contact_support(self):
        Support().contact_support.click()
        time.sleep(4)
        browser.driver.switch_to_window(browser.driver.window_handles.pop())
        self.assertIn('http://software.mirantis.com/',
                      browser.driver.current_url)

    def test_diagnostic_snapshot(self):
        Support().generate_snapshot.click()
        with Support() as s:
            PageObject.wait_element(s, 'download_snapshot')
            self.assertTrue(
                s.download_snapshot.is_enabled(),
                '"Diagnostic Snapshot" is displayed')

    def test_capacity_audit(self):
        Support().view_capacity_audit.click()
        self.assertEqual(
            'Home/ Support/ Capacity',
            Header().breadcrumb.text,
            'Breadcrumb text'
        )
