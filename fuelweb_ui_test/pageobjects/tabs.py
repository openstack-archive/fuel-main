from pageobjects.base import PageObject


class Tabs(PageObject):

    XPATH_TAB = '//ul/li/a[div/text()="{}"]'

    @property
    def nodes(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_TAB.format('Nodes'))

    @property
    def networks(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_TAB.format('Networks'))

    @property
    def settings(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_TAB.format('Settings'))

    @property
    def logs(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_TAB.format('Logs'))

    @property
    def health_check(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_TAB.format('Health Check'))

    @property
    def actions(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_TAB.format('Actions'))
