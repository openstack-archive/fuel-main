from pageobjects.base import PageObject
from pageobjects.settings import SettingsFooter
from selenium.webdriver.support.select import Select


class InterfacesSettings(PageObject, SettingsFooter):

    @property
    def interfaces(self):
        elements = self.parent.\
            find_elements_by_css_selector('.physical-network-box')
        return [Interface(e) for e in elements]


class Interface(PageObject):

    def __init__(self, element):
        PageObject.__init__(self, element)

    @property
    def info(self):
        return self.parent.find_element_by_css_selector('.network-info-box')

    @property
    def networks_box(self):
        return self.parent.find_element_by_css_selector('.logical-network-box')

    @property
    def networks(self):
        elements = self.parent.\
            find_elements_by_css_selector('.logical-network-item')
        return {el.find_element_by_css_selector('.name').text.lower(): el
                for el in elements}

    @property
    def interface_checkbox(self):
        return self.parent.find_element_by_css_selector('.custom-tumbler')

    @property
    def bond_mode(self):
        return self.parent.find_element_by_css_selector('.network-bond-mode')

    @property
    def select_mode(self):
        return Select(
            self.parent.find_element_by_css_selector('select[name=mode]'))
