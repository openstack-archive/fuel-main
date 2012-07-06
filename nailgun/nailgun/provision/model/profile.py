import logging
from . import ModelObject, Validator
from nailgun.provision import ProvisionException


class Profile(ModelObject):
    _arch = None
    _kernel = None
    _initrd = None
    _os = None
    _osversion = None
    _seed = None
    _kopts = ""

    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger('provision.model.profile')

    def save(self):
        if not Validator.is_platform_valid(
                self._os, self._osversion, self._arch
            ):
            raise ProvisionException("Platform is not valid")
        self.driver.save_profile(self)

    @property
    def arch(self):
        if not self._arch:
            raise ProvisionException("Arch is not set properly")
        return self._arch

    @arch.setter
    def arch(self, arch):
        if not Validator.is_arch_valid(arch):
            raise ProvisionException("Arch is not valid")
        self._arch = arch

    @property
    def kernel(self):
        if not self._kernel:
            raise ProvisionException("Kernel is not set properly")
        return self._kernel

    @kernel.setter
    def kernel(self, kernel):
        self._kernel = kernel

    @property
    def initrd(self):
        if not self._initrd:
            raise ProvisionException("Initrd is not set properly")
        return self._initrd

    @initrd.setter
    def initrd(self, initrd):
        self._initrd = initrd

    @property
    def os(self):
        if not self._os:
            raise ProvisionException("Os is not set properly")
        return self._os

    @os.setter
    def os(self, os):
        if not Validator.is_os_valid(os):
            raise ProvisionException("Os is not valid")
        self._os = os

    @property
    def osversion(self):
        if not self._osversion:
            raise ProvisionException("Osversion is not set properly")
        return self._osversion

    @osversion.setter
    def osversion(self, osversion):
        if not Validator.is_osversion_valid(osversion):
            raise ProvisionException("Osversion is not valid")
        self._osversion = osversion

    @property
    def seed(self):
        if not self._seed:
            raise ProvisionException("Seed is not set properly")
        self.logger.debug("Profile seed getter: %s" % self._seed)
        return self._seed

    @seed.setter
    def seed(self, seed):
        self.logger.debug("Profile seed setter: %s" % seed)
        self._seed = seed

    @property
    def kopts(self):
        self.logger.debug("Profile kopts getter: %s" % self._kopts)
        return self._kopts

    @kopts.setter
    def kopts(self, kopts):
        self.logger.debug("Profile kopts setter: %s" % kopts)
        self._kopts = kopts
