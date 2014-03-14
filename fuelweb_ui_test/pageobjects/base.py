from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.wait import WebDriverWait
import browser
import time


class PageObject:

    XPATH_RADIO = '//div[@class="custom-tumbler" ' \
                  'and input[@type="radio" and @name="{}" and @value="{}"]]'

    XPATH_CHECKBOX = \
        '//div[@class="custom-tumbler" ' \
        'and input[@type="checkbox" and @name="{}"]]'

    def __init__(self, parent=None):
        self.parent = parent or browser.driver

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def wait_until_moving(element, timeout=10):
        class Move:
            def __init__(self, elem):
                self.element = elem
                self.location = elem.location

            def __call__(self, *args, **kwargs):
                loc = element.location
                res = self.location['x'] == loc['x'] \
                    and self.location['y'] == loc['y']
                self.location = loc
                return res

        wait = WebDriverWait(browser.driver, timeout)
        wait.until(Move(element))

    @staticmethod
    def wait_until_exists(element, timeout=10):
        wait = WebDriverWait(browser.driver, timeout)
        try:
            wait.until(lambda driver: not element.is_displayed())
        except StaleElementReferenceException:
            pass

    @staticmethod
    def wait_element(page_object, attribute, timeout=10):
        class El:
            def __init__(self, page_object, attribute):
                self.page_object = page_object
                self.attribute = attribute

            def __call__(self, *args, **kwargs):
                try:
                    getattr(self.page_object, attribute)
                    return True
                except NoSuchElementException:
                    return False

        wait = WebDriverWait(browser.driver, timeout)
        wait.until(El(page_object, attribute))

    @staticmethod
    def long_wait_element(page_object, attribute, timeout=40):
        class El:
            def __init__(self, page_object, attribute):
                self.page_object = page_object
                self.attribute = attribute

            def __call__(self, *args, **kwargs):
                try:
                    getattr(self.page_object, attribute)
                    return True
                except (NoSuchElementException,
                        StaleElementReferenceException):
                    return False

        wait = WebDriverWait(browser.driver, timeout)
        wait.until(El(page_object, attribute))

    @staticmethod
    def click_element(page_object, *args):
        attributes = [attribute for attribute in args]
        attempts = 0
        while attempts < 3:
            try:
                if len(attributes) == 1:
                    getattr(page_object, attributes[0]).click()
                elif len(attributes) == 3:
                    getattr(getattr(page_object, attributes[0])
                            [attributes[2]], attributes[1]).click()
                elif len(attributes) == 4:
                    getattr(getattr(getattr(page_object,
                                            attributes[0])[attributes[3]],
                                    attributes[1]), attributes[2]).click()
                break
            except StaleElementReferenceException:
                pass
            attempts += 1

    @staticmethod
    def find_element(page_object, *args):
        attributes = [attribute for attribute in args]
        attempts = 0
        while attempts < 3:
            try:
                if len(attributes) == 1:
                    getattr(page_object, attributes[0])
                elif len(attributes) == 3:
                    getattr(getattr(page_object,
                                    attributes[0])[attributes[2]],
                            attributes[1])
                elif len(attributes) == 4:
                    getattr(getattr(getattr(page_object,
                                            attributes[0])[attributes[3]],
                                    attributes[1]), attributes[2])
                break
            except StaleElementReferenceException:
                pass
            attempts += 1


class Popup(PageObject):

    def __init__(self):
        element = browser.driver.find_element_by_css_selector('div.modal')
        PageObject.__init__(self, element)
        time.sleep(0.5)
        #PageObject.wait_until_moving(self.parent)

    def wait_until_exists(self):
        try:
            PageObject.wait_until_exists(
                browser.driver.
                find_element_by_css_selector('div.modal-backdrop'))
        except NoSuchElementException:
            pass

    @property
    def close_cross(self):
        return self.parent.find_element_by_css_selector('.close')

    @property
    def header(self):
        return self.parent.find_element_by_css_selector('.modal-header > h3')


class ConfirmPopup(Popup):

    TEXT = 'Settings were modified but not saved'

    @property
    def stay_on_page(self):
        return self.parent.find_element_by_css_selector('.btn-return')

    @property
    def leave_page(self):
        return self.parent.find_element_by_css_selector('.proceed-btn')
