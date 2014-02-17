from pageobjects.base import PageObject, Popup


class Actions(PageObject):

    @property
    def name(self):
        return self.parent.find_element_by_css_selector('.rename-cluster-form input')

    @property
    def rename(self):
        return self.parent.find_element_by_css_selector('button.apply-name-btn')

    @property
    def delete(self):
        return self.parent.find_element_by_css_selector('button.delete-cluster-btn')


class DeleteEnvironmentPopup(Popup):

    @property
    def delete(self):
        return self.parent.find_element_by_css_selector('button.remove-cluster-btn')