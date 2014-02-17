from selenium.webdriver.support.select import Select
from pageobjects.base import PageObject
from pageobjects.base import Popup


class Environments(PageObject):

    @property
    def create_cluster_box(self):
        return self.parent.find_element_by_css_selector('div.create-cluster')

    @property
    def create_cluster_boxes(self):
        return self.parent.find_elements_by_css_selector('a.clusterbox')


class RedhatAccountPopup(Popup):

    @property
    def license_rhsm(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('license-type', 'rhsm'))

    @property
    def license_rhn(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('license-type', 'rhn'))

    @property
    def redhat_username(self):
        return self.parent.find_element_by_name('username')

    @property
    def redhat_password(self):
        return self.parent.find_element_by_name('password')

    @property
    def redhat_satellite(self):
        return self.parent.find_element_by_name('satellite')

    @property
    def redhat_activation_key(self):
        return self.parent.find_element_by_name('activation_key')

    @property
    def apply(self):
        return self.parent.\
            find_element_by_css_selector('button.btn-os-download')


class Wizard(Popup, RedhatAccountPopup):

    @property
    def name(self):
        return self.parent.find_element_by_name('name')

    @property
    def release(self):
        return Select(self.parent.find_element_by_name('release'))

    @property
    def next(self):
        return self.parent.find_element_by_css_selector('button.next-pane-btn')

    @property
    def create(self):
        return self.parent.find_element_by_css_selector('button.finish-btn')

    @property
    def cancel(self):
        return self.parent.\
            find_element_by_css_selector('button.btn[data-dismiss=modal]')

    @property
    def prev(self):
        return self.parent.find_element_by_css_selector('button.prev-pane-btn')

    @property
    def mode_multinode(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_RADIO.format('mode', 'multinode'))

    @property
    def mode_ha_compact(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('mode', 'ha_compact'))

    @property
    def hypervisor_kvm(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_RADIO.format('hypervisor', 'kvm'))

    @property
    def hypervisor_qemu(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('hypervisor', 'qemu'))

    @property
    def network_nova(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('manager', 'nova-network'))

    @property
    def network_neutron_gre(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('manager', 'neutron-gre'))

    @property
    def network_neutron_vlan(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('manager', 'neutron-vlan'))

    @property
    def storage_cinder_default(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('cinder', 'default'))

    @property
    def storage_cinder_ceph(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('cinder', 'ceph'))

    @property
    def storage_glance_default(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('glance', 'default'))

    @property
    def storage_glance_ceph(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('glance', 'ceph'))

    @property
    def install_savanna(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_CHECKBOX.format('savanna'))

    @property
    def install_murano(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_CHECKBOX.format('murano'))

    @property
    def install_ceilometer(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_CHECKBOX.format('ceilometer'))


class DeployChangesPopup(Popup):

    @property
    def deploy(self):
        return self.parent.\
            find_element_by_css_selector('.start-deployment-btn')


class DiscardChangesPopup(Popup):

    @property
    def discard(self):
        return self.parent.find_element_by_css_selector('.discard-btn')
