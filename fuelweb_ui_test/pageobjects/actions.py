import time

from pageobjects.base import PageObject
from pageobjects.base import Popup
from pageobjects.tabs import Tabs


class Actions(PageObject):

    @property
    def name(self):
        return self.parent.\
            find_element_by_css_selector('.environment-action-form input')

    @property
    def rename(self):
        return self.parent.\
            find_element_by_css_selector('button.rename-environment-btn')

    @property
    def delete(self):
        return self.parent.\
            find_element_by_css_selector('button.delete-environment-btn')

    @property
    def reset(self):
        return self.parent.\
            find_element_by_css_selector('button.reset-environment-btn')

    @property
    def reset_popup(self):
        return self.parent.\
            find_element_by_xpath("//div[@class='modal-footer']/button"
                                  "[contains(@class,'reset-environment-btn')]")

    @property
    def stop(self):
        return self.parent.\
            find_element_by_css_selector('button.stop-deployment-btn')

    @property
    def progress(self):
        return self.parent.find_element_by_css_selector('.progress')

    @property
    def pending_nodes(self):
        return self.parent.\
            find_element_by_xpath("//span[text()='Pending Addition']")

    @property
    def cancel_popup(self):
        return self.parent.\
            find_element_by_xpath("//button[text()='Cancel']")

    @property
    def verify_disabled_deploy(self):
        return self.parent.find_element_by_xpath(
            "//div[@class='deployment-control-item-box']/button[@disabled]")

    @property
    def stop_deploy(self):
        return self.parent.find_element_by_css_selector('button.'
                                                        'stop-deployment-btn')

    @property
    def stop_deploy_popup(self):
        return self.parent.\
            find_element_by_xpath("//div[@class='modal-footer']/button"
                                  "[contains(@class,'stop-deployment-btn')]")

    @classmethod
    def reset_env(cls):
        PageObject.click_element(Actions(), 'reset')
        PageObject.wait_element(Actions(), 'reset_popup')
        time.sleep(2)
        PageObject.click_element(Actions(), 'reset_popup')
        PageObject.click_element(Tabs(), 'nodes')
        PageObject.long_wait_element(Actions(), 'pending_nodes')

    @classmethod
    def cancel_reset(cls):
        Actions().reset.click()
        PageObject.click_element(Actions(), 'cancel_popup')
        PageObject.click_element(Tabs(), 'nodes')

    @classmethod
    def stop_deploy_process(cls):
        PageObject.click_element(Actions(), 'stop_deploy')
        PageObject.wait_element(Actions, "stop_deploy_popup")
        PageObject.click_element(Actions(), 'stop_deploy_popup')
        PageObject.click_element(Tabs(), 'nodes')
        PageObject.long_wait_element(Actions(), 'pending_nodes')


class DeleteEnvironmentPopup(Popup):
    @property
    def delete(self):
        return self.parent.\
            find_element_by_css_selector(
                'button.remove-cluster-btn')
