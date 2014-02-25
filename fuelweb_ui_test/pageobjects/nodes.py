from selenium.webdriver.support.select import Select
from pageobjects.base import PageObject
from pageobjects.base import Popup


class Nodes(PageObject):

    @property
    def info_icon(self):
        return self.parent.find_element_by_css_selector('i.icon-info-circled')

    @property
    def env_name(self):
        return self.parent.\
            find_element_by_css_selector('span.btn-cluster-details')

    @property
    def deploy_changes(self):
        return self.parent.find_element_by_css_selector('button.deploy-btn')

    @property
    def discard_changes(self):
        return self.parent.find_element_by_css_selector('button.rollback')

    @property
    def progress_deployment(self):
        return self.parent.find_element_by_css_selector('.progress-deploy')

    @property
    def env_details(self):
        return self.parent.find_element_by_css_selector('ul.cluster-details')

    @property
    def group_by(self):
        return Select(
            self.parent.find_element_by_css_selector('select[name=grouping]'))

    @property
    def add_nodes(self):
        return self.parent.find_element_by_css_selector('button.btn-add-nodes')

    @property
    def delete_nodes(self):
        return self.parent.\
            find_element_by_css_selector('button.btn-delete-nodes')

    @property
    def edit_roles(self):
        return self.parent.\
            find_element_by_css_selector('button.btn-edit-nodes')

    @property
    def configure_interfaces(self):
        return self.parent.\
            find_element_by_css_selector('button.btn-configure-interfaces')

    @property
    def apply_changes(self):
        return self.parent.find_element_by_css_selector('button.btn-apply')

    @property
    def configure_disks(self):
        return self.parent.\
            find_element_by_css_selector('button.btn-configure-disks')

    @property
    def nodes(self):
        elements = self.parent.find_elements_by_css_selector('.node-container')
        return [NodeContainer(el) for el in elements]

    @property
    def nodes_discovered(self):
        elements = self.parent.\
            find_elements_by_css_selector('.node-container.discover')
        return [NodeContainer(el) for el in elements]

    @property
    def nodes_offline(self):
        elements = self.parent.\
            find_elements_by_css_selector('.node-container.node-offline')
        return [NodeContainer(el) for el in elements]

    @property
    def nodes_error(self):
        elements = self.parent.\
            find_elements_by_css_selector('.node-container.error')
        return [NodeContainer(el) for el in elements]

    @property
    def select_all(self):
        return self.parent.\
            find_element_by_css_selector('[name=select-nodes-common]')

    @property
    def select_all_in_group(self):
        return self.parent.\
            find_elements_by_css_selector('[name=select-node-group]')

    @property
    def node_groups(self):
        elements = self.parent.find_elements_by_css_selector('.node-groups')
        return [Nodes(el) for el in elements]

    @classmethod
    def add_controller_compute_nodes(cls):
        PageObject.click_element(Nodes(), 'add_nodes')
        Nodes().nodes_discovered[0].checkbox.click()
        RolesPanel().controller.click()
        Nodes().apply_changes.click()
        PageObject.wait_until_exists(Nodes().apply_changes)
        PageObject.click_element(Nodes(), 'add_nodes')
        PageObject.click_element(Nodes(), 'nodes_discovered', 'checkbox', 0)
        RolesPanel().compute.click()
        Nodes().apply_changes.click()
        PageObject.wait_until_exists(Nodes().apply_changes)


class NodeContainer(PageObject):

    @property
    def name(self):
        return self.parent.find_element_by_css_selector('div.name > p')

    @property
    def name_input(self):
        return self.parent.find_element_by_css_selector('div.name > input')

    @property
    def checkbox(self):
        return self.parent.find_element_by_css_selector('div.node-checkbox')

    @property
    def roles(self):
        return self.parent.find_element_by_css_selector('div.role-list')

    @property
    def details(self):
        return self.parent.find_element_by_css_selector('.node-details')

    @property
    def status(self):
        return self.parent.find_element_by_css_selector('.node-status-label')


class RolesPanel(PageObject):

    XPATH_ROLE = '//label[contains(., "{}")]/input'

    @property
    def controller(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_ROLE.format('Controller'))

    @property
    def compute(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_ROLE.format('Compute'))

    @property
    def cinder(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_ROLE.format('Cinder'))

    @property
    def ceph_osd(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_ROLE.format('Ceph OSD'))


class NodeInfo(Popup):

    @property
    def edit_networks(self):
        return self.parent.find_element_by_css_selector('.btn-edit-networks')

    @property
    def edit_disks(self):
        return self.parent.find_element_by_css_selector('.btn-edit-disks')

    @property
    def close(self):
        return self.parent.find_element_by_css_selector('.node-modal-close')


class DeleteNodePopup(Popup):

    @property
    def delete(self):
        return self.parent.find_element_by_css_selector('.btn-delete')
