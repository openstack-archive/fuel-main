from pageobjects.base import PageObject
from pageobjects.settings import SettingsFooter


class DisksSettings(PageObject, SettingsFooter):

    @property
    def disks(self):
        elements = self.parent.\
            find_elements_by_css_selector('div.node-disks > div')
        return [Disk(el) for el in elements]


class Disk(PageObject):

    XPATH_INFORMATION_ITEM = './/div[@class="disk-map-details-item" and ' \
                             'div[@class="disk-map-details-name"]="{}"]' \
                             '/div[@class="disk-map-details-parameter"]'

    def __init__(self, element):
        PageObject.__init__(self, element)

    @property
    def volume_os(self):
        return Volume(self.parent.find_element_by_css_selector(
            'div.volume-group.os > .toggle-volume'))

    @property
    def volume_image(self):
        return Volume(self.parent.find_element_by_css_selector(
            'div.volume-group.image > .toggle-volume'))

    @property
    def volume_storage(self):
        return Volume(self.parent.find_element_by_css_selector(
            'div.volume-group.vm > .toggle-volume'))

    @property
    def volume_unallocated(self):
        return Volume(self.parent.find_element_by_css_selector(
            'div.volume-group.unallocated > .toggle-volume'))

    @property
    def volume_group_os(self):
        return VolumeGroup(self.parent.find_element_by_css_selector(
            'div.volume-group-box[data-volume=os]'
        ))

    @property
    def volume_group_image(self):
        return VolumeGroup(self.parent.find_element_by_css_selector(
            'div.volume-group-box[data-volume=image]'
        ))

    @property
    def volume_group_storage(self):
        return VolumeGroup(self.parent.find_element_by_css_selector(
            'div.volume-group-box[data-volume=vm]'
        ))

    @property
    def details_panel(self):
        return self.parent.find_element_by_css_selector('.disk-map-details')

    @property
    def name(self):
        return self.parent.find_element_by_xpath(
            self.XPATH_INFORMATION_ITEM.format('name'))

    @property
    def model(self):
        return self.parent.find_element_by_xpath(
            self.XPATH_INFORMATION_ITEM.format('model'))

    @property
    def disk(self):
        return self.parent.find_element_by_xpath(
            self.XPATH_INFORMATION_ITEM.format('disk'))

    @property
    def size(self):
        return self.parent.find_element_by_xpath(
            self.XPATH_INFORMATION_ITEM.format('size'))


class Volume(PageObject):

    def __init__(self, element):
        PageObject.__init__(self, element)

    @property
    def name(self):
        return self.parent.find_element_by_css_selector('.volume-group-name')

    @property
    def size(self):
        return self.parent.find_element_by_css_selector('.volume-group-size')

    @property
    def close_cross(self):
        return self.parent.\
            find_element_by_xpath('./../div[contains(@class, "close-btn")]')


class VolumeGroup(PageObject):

    def __init__(self, element):
        PageObject.__init__(self, element)

    @property
    def name(self):
        return self.parent.\
            find_element_by_css_selector('.volume-group-box-name')

    @property
    def use_all(self):
        return self.parent.find_element_by_css_selector('.use-all-allowed')

    @property
    def input(self):
        return self.parent.find_element_by_tag_name('input')
