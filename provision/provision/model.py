import re
from . import ProvisionException

class ModelObject(object):
    _driver = None

    @property
    def driver(self):
        if self._driver is None:
            raise ProvisionException, "Driver is not set properly."
        return self._driver

    @driver.setter
    def driver(self, driver):
        self._driver = driver

class Validator:
    _supported_os = (
        "ubuntu", 
        "redhat",
        )

    _supported_osversion = (
        "precise",
        "rhel6",
        )

    _supported_arch = (
        "x86_64",
        )

    _supported_platform = (
        ("ubuntu", "precise", "x86_64"),
        ("redhat", "rhel6", "x86_64"),
        )

    @classmethod
    def is_os_valid(cls, os):
        return os in cls._supported_os

    @classmethod
    def is_osversion_valid(cls, osversion):
        return osversion in cls._supported_osversion

    @classmethod
    def is_arch_valid(cls, arch):
        return arch in cls._supported_arch

    @classmethod
    def is_platform_valid(cls, os, osversion, arch):
        return (os, osversion, arch) in cls._supported_platform
        
class Profile(ModelObject):
    _arch = None
    _kernel = None
    _initrd = None
    _os = None
    _osversion = None
    _seed = None

    def __init__(self, name):
        self.name = name

    def save(self):
        if not Validator.is_platform_valid(self._os, self._osversion, self._arch):
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
        return self._seed

    @osversion.setter
    def seed(self, seed):
        self._seed = seed


class Node(ModelObject):
    def __init__(self, name):
        self.name = name
        
    def save(self):
        self.driver.save_node(self)

    def install(self):
        raise NotImplementedError

    def power_on(self):
        raise NotImplementedError

    def power_off(self):
        raise NotImplementedError


