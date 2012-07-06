import logging
from nailgun.provision import ProvisionException
from . import ModelObject, Validator


class Node(ModelObject):
    _mac = None
    _profile = None
    _kopts = ""
    _pxe = False
    _power = None

    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger('provision.model.node')

    def save(self):
        self.driver.save_node(self)

    @property
    def mac(self):
        if not self._mac:
            raise ProvisionException("Mac is not set properly")
        return self._mac

    @mac.setter
    def mac(self, mac):
        if not Validator.is_mac_valid(mac):
            raise ProvisionException("Mac is not valid")
        self._mac = mac

    @property
    def profile(self):
        if not self._profile:
            raise ProvisionException("Profile is not set properly")
        return self._profile

    @profile.setter
    def profile(self, profile):
        if not Validator.is_profile_valid(profile):
            raise ProvisionException("Profile is not valid")
        self._profile = profile

    @property
    def kopts(self):
        self.logger.debug("Node kopts getter: %s" % self._kopts)
        return self._kopts

    @kopts.setter
    def kopts(self, kopts):
        self.logger.debug("Node kopts setter: %s" % kopts)
        self._kopts = kopts

    @property
    def pxe(self):
        self.logger.debug("Node pxe getter: %s" % str(self._pxe))
        return self._pxe

    @pxe.setter
    def pxe(self, pxe):
        self.logger.debug("Node pxe setter: %s" % str(pxe))
        if pxe:
            self._pxe = True
        self._pxe = False

    @property
    def power(self):
        if not self._power:
            raise ProvisionException("Power is not set properly")
        return self._power

    @power.setter
    def power(self, power):
        if not Validator.is_power_valid(power):
            raise ProvisionException("Power is not valid")
        self._power = power

    def power_on(self):
        self.driver.power_on(self)

    def power_off(self):
        self.driver.power_off(self)

    def power_reboot(self):
        self.driver.power_reboot(self)

    def power_status(self):
        self.driver.power_status(self)
