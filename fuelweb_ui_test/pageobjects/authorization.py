from base import PageObject
#This class contains properties and methods for authorization in fuel ui interface
#author: Tatyana Dubyk /6th of  Aug 2014


class Authorization(PageObject):
    @property
    def authorization_window(self):
        return self.parent.\
            find_element_by_css_selector(".login-box")

    @property
    def login_inputfield(self):
        return self.parent.\
            find_element_by_css_selector("input[name='username']")

    @property
    def password_inputfield(self):
        return self.parent.\
            find_element_by_css_selector("input[name='password']")

    @property
    def login_button(self):
        return self.parent.\
            find_element_by_css_selector(".btn.btn-success.login-btn")


