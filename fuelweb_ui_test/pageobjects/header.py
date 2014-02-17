import browser
from decorators import implicit_wait
from pageobjects.base import PageObject


class Header(PageObject):

    @property
    def logo(self):
        return self.parent.find_element_by_css_selector('div.logo')

    @property
    def environments(self):
        return self.parent.\
            find_element_by_css_selector('.navigation-bar-ul '
                                         'a[href$=clusters]')

    @property
    def releases(self):
        return self.parent.\
            find_element_by_css_selector('.navigation-bar-ul '
                                         'a[href$=releases]')

    @property
    def support(self):
        return self.parent.\
            find_element_by_css_selector('.navigation-bar-ul a[href$=support]')

    @property
    def breadcrumb(self):
        return self.parent.find_element_by_css_selector('.breadcrumb')

    @property
    def total_nodes(self):
        return self.parent.\
            find_element_by_css_selector('div.total-nodes-count')

    @property
    def unallocated_nodes(self):
        return self.parent.\
            find_element_by_css_selector('div.unallocated-nodes-count')


class TaskResultAlert(PageObject):

    @implicit_wait(60)
    def __init__(self):
        element = browser.driver.\
            find_element_by_css_selector('div.task-result')
        PageObject.__init__(self, element)

    @property
    def close(self):
        return self.parent.find_element_by_css_selector('button.close')

    @property
    def header(self):
        return self.parent.find_element_by_css_selector('h4')
