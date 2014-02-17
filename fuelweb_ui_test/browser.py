from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from settings import *

driver = None


def start_driver(browser=None):
    browser = browser or BROWSER

    def start_chrome():
        return webdriver.Chrome(
            executable_path=CHROME_EXECUTABLE_PATH,
            desired_capabilities=DesiredCapabilities.CHROME)

    def start_firefox():
        return webdriver.Firefox()

    def start_iexplore():
        return webdriver.Ie()

    global driver
    if browser == "iexplore":
        driver = start_iexplore()
    elif browser == "chrome":
        driver = start_chrome()
    elif browser == "firefox":
        driver = start_firefox()

    #driver.set_window_size(1024, 768)
    driver.maximize_window()
    driver.implicitly_wait(SELENIUM_IMPLICIT_WAIT)
    return driver


def quit_driver():
    driver.quit()