from pageobjects.base import PageObject


class Support(PageObject):

    @property
    def register_fuel(self):
        return self.parent.find_element_by_link_text('Register Fuel')

    @property
    def contact_support(self):
        return self.parent.find_element_by_link_text('Contact Support')

    @property
    def generate_snapshot(self):
        return self.parent.find_element_by_css_selector('.snapshot > button')

    @property
    def download_snapshot(self):
        return self.parent.\
            find_element_by_css_selector('span.ready > a')

    @property
    def view_capacity_audit(self):
        return self.parent.find_element_by_link_text('View Capacity Audit')

    @property
    def capacity_report(self):
        return self.parent.find_element_by_css_selector('.btn.btn-info')
