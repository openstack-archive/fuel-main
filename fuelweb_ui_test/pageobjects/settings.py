from pageobjects.base import PageObject


class SettingsFooter(PageObject):

    @property
    def back_to_node_list(self):
        return self.parent.\
            find_element_by_xpath('//button[text()="Back To Node List"]')

    @property
    def load_defaults(self):
        return self.parent.\
            find_element_by_xpath('//button[text()="Load Defaults"]')

    @property
    def cancel_changes(self):
        return self.parent.\
            find_element_by_xpath('//button[text()="Cancel Changes"]')

    @property
    def save_settings(self):
        return self.parent.\
            find_element_by_xpath('//button[text()="Save Settings"]')

    @property
    def apply(self):
        return self.parent.find_element_by_xpath('//button[text()="Apply"]')

    @property
    def bond_interfaces(self):
        return self.parent.find_element_by_css_selector('button.btn-bond')

    @property
    def unbond_interfaces(self):
        return self.parent.find_element_by_css_selector('button.btn-unbond')


class Settings(PageObject, SettingsFooter):

    @property
    def username(self):
        return self.parent.find_element_by_name('access.user')

    @property
    def password(self):
        return self.parent.find_element_by_name('access.password')

    @property
    def show_password(self):
        return self.parent.\
            find_element_by_xpath('//div[input[@name="access.password"]]/span')

    @property
    def tenant(self):
        return self.parent.find_element_by_name('access.tenant')

    @property
    def email(self):
        return self.parent.find_element_by_name('access.email')

    @property
    def install_savanna(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_CHECKBOX.format('additional_components.sahara'))

    @property
    def install_murano(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_CHECKBOX.format('additional_components.murano'))

    @property
    def install_ceilometer(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_CHECKBOX.format('additional_components.ceilometer'))

    @property
    def debug(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_CHECKBOX.format('common.debug'))

    @property
    def hypervisor_kvm(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_RADIO.format('common.libvirt_type',
                                                          'kvm'))

    @property
    def hypervisor_qemu(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_RADIO.format('common.libvirt_type',
                                                          'qemu'))

    @property
    def assign_ip(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_CHECKBOX.format('common.auto_assign_floating_ip'))

    @property
    def filter_scheduler(self):
        return self.parent.find_element_by_xpath(
            self.XPATH_RADIO.format(
                'common.compute_scheduler_driver',
                'nova.scheduler.filter_scheduler.FilterScheduler'))

    @property
    def simple_scheduler(self):
        return self.parent.find_element_by_xpath(
            self.XPATH_RADIO.format(
                'common.compute_scheduler_driver',
                'nova.scheduler.simple.SimpleScheduler'))

    @property
    def vlan_splinters(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_CHECKBOX.format('vlan_splinters'))

    @property
    def vlan_splinters_disabled(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('vlan_splinters', 'disabled'))

    @property
    def vlan_splinters_soft(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('vlan_splinters.vswitch', 'soft'))

    @property
    def vlan_splinters_hard(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_RADIO.format('vlan_splinters.vswitch', 'hard'))

    @property
    def use_cow_images(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_CHECKBOX.format('common.use_cow_images'))

    @property
    def start_guests(self):
        return self.parent.\
            find_element_by_xpath(
                self.XPATH_CHECKBOX.format('common.start_guests_on_host_boot'))

    @property
    def auth_key(self):
        return self.parent.find_element_by_name('common.auth_key')

    @property
    def syslog_server(self):
        return self.parent.find_element_by_name('syslog.syslog_server')

    @property
    def syslog_port(self):
        return self.parent.find_element_by_name('syslog.syslog_port')

    @property
    def syslog_udp(self):
        return self.parent.find_element_by_xpath(
            self.XPATH_RADIO.format(
                'syslog.syslog_transport', 'udp'))

    @property
    def syslog_tcp(self):
        return self.parent.find_element_by_xpath(
            self.XPATH_RADIO.format(
                'syslog.syslog_transport', 'tcp'))

    @property
    def cinder_for_volumes(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_CHECKBOX.format('storage.volumes_lvm'))

    @property
    def ceph_for_volumes(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_CHECKBOX.format('storage.volumes_ceph'))

    @property
    def ceph_for_images(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_CHECKBOX.format('storage.images_ceph'))

    @property
    def ceph_ephemeral(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_CHECKBOX.format('storage.ephemeral_ceph'))

    @property
    def ceph_rados_gw(self):
        return self.parent.\
            find_element_by_xpath(self.XPATH_CHECKBOX.format('storage.objects_ceph'))

    @property
    def ceph_factor(self):
        return self.parent.find_element_by_name('storage.osd_pool_size')
