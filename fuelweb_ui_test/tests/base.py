import base64
from io import BytesIO
from unittest import TestCase
from PIL import Image
import operator
import math
from selenium.common.exceptions import NoSuchElementException
import time
import browser
from pageobjects.header import Header
from settings import FOLDER_SCREEN_CURRENT
from settings import FOLDER_SCREEN_EXPECTED
from settings import NAILGUN_FIXTURES
from settings import URL_HOME


class BaseTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        browser.start_driver()
        cls.clear_nailgun_database()

    @classmethod
    def tearDownClass(cls):
        browser.quit_driver()

    def setUp(self):
        self.get_home()

    @staticmethod
    def get_home():
        for i in range(5):
            try:
                browser.driver.get(URL_HOME)
                Header().logo.is_displayed()
                browser.driver.execute_script('jQuery.fx.off = true')
                browser.driver.execute_script('''
                    $('head').append(
                        '<style type="text/css">
                            * {
                        -webkit-transition-duration: 0.00000001s !important;
                        -moz-transition: 0.00000001s !important;
                        transition-duration: 0.00000001s !important;
                            }
                        </style>')
                '''.replace('\n', ''))
                break
            except NoSuchElementException:
                pass

    @staticmethod
    def refresh():
        for i in range(5):
            try:
                browser.driver.refresh()
                time.sleep(0.5)
                Header().logo.is_displayed()
                break
            except NoSuchElementException:
                pass

    @staticmethod
    def clear_nailgun_database():
        from nailgun.db import dropdb
        from nailgun.db import syncdb
        from nailgun.db.sqlalchemy import fixman
        dropdb()
        syncdb()
        fixman.upload_fixtures()
        for fixture in NAILGUN_FIXTURES.split(':'):
            if fixture == '':
                continue
            with open(fixture, "r") as fileobj:
                fixman.upload_fixture(fileobj)

    def assert_screen(self, name):
        img_exp = Image.open('{}/{}.png'.format(FOLDER_SCREEN_EXPECTED, name))

        img_cur_base64 = browser.driver.get_screenshot_as_base64()
        img_cur = Image.open(BytesIO(base64.decodestring(img_cur_base64)))
        img_cur.save('{}/{}.png'.format(FOLDER_SCREEN_CURRENT, name))

        h1 = img_exp.histogram()
        h2 = img_cur.histogram()
        rms = math.sqrt(reduce(operator.add, map(lambda a, b: (a - b) ** 2,
                        h1, h2)) / len(h1))

        self.assertNotEqual(rms == 0, 'Screen valid')
