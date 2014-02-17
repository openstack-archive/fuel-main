from pageobjects.base import PageObject


class Releases(PageObject):

    @property
    def dict(self):
        elements = self.parent.\
            find_elements_by_css_selector('div.table-releases-box tbody > tr')
        return {Release(el).name.text: Release(el) for el in elements}

    @property
    def rhel_setup(self):
        return self.parent.find_element_by_css_selector('.btn-rhel-setup')


class Release(PageObject):

    def __init__(self, element):
        PageObject.__init__(self, parent=element)

    @property
    def name(self):
        return self.parent.find_element_by_css_selector('.release-name')

    @property
    def version(self):
        return self.parent.find_element_by_css_selector('.release-version')

    @property
    def status(self):
        return self.parent.find_element_by_css_selector('.release-status')

    @property
    def download_progress(self):
        return self.parent.find_element_by_css_selector('.download_progress')
