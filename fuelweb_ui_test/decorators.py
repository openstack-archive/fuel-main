import browser
from fuelweb_ui_test.settings import SELENIUM_IMPLICIT_WAIT


def implicit_wait(wait_time):
    def wrapper(func):
        def wrapped(*args, **kwargs):
            browser.driver.implicitly_wait(wait_time)
            result = func(*args, **kwargs)
            browser.driver.implicitly_wait(SELENIUM_IMPLICIT_WAIT)
            return result
        return wrapped
    return wrapper
