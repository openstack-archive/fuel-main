from pageobjects.base import PageObject
from pageobjects.settings import SettingsFooter


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
