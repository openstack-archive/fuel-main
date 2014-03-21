from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from fuelweb_ui_test.settings import BROWSER
from fuelweb_ui_test.settings import CHROME_EXECUTABLE_PATH
from fuelweb_ui_test.settings import SELENIUM_IMPLICIT_WAIT
from pyvirtualdisplay import Display

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

    def start_headless():
        display = Display(visible=0, size=(1024, 768))
        display.start()
        return webdriver.Chrome(
            executable_path=CHROME_EXECUTABLE_PATH,
            desired_capabilities=DesiredCapabilities.CHROME)

    global driver
    if browser == "iexplore":
        driver = start_iexplore()
    elif browser == "chrome":
        driver = start_chrome()
    elif browser == "firefox":
        driver = start_firefox()
    elif browser == "headless":
        driver = start_headless()

    #driver.set_window_size(1024, 768)
    driver.maximize_window()
    driver.implicitly_wait(SELENIUM_IMPLICIT_WAIT)
    return driver


def quit_driver():
    driver.quit()
