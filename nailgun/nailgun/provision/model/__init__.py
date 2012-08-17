import re
from nailgun.provision import ProvisionException
import logging


class ModelObject(object):
    _driver = None

    @property
    def driver(self):
        if self._driver is None:
            raise ProvisionException("Driver is not set properly.")
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

    _supported_powertypes = (
        "virsh",
        "ssh",
        )

    @classmethod
    def is_mac_valid(cls, mac):
        rex = re.compile(ur'^([0-9abcdef]{2}:){5}[0-9abcdef]{2}$', re.I)
        return rex.match(mac)

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

    # FIXME
    # IT IS NEEDED TO BE CHECKED IF PROVISION ALREADY HAS THAT PROFILE
    # IF NOT THEN PROFILE IS OBVIOUSLY INVALID
    @classmethod
    def is_profile_valid(cls, profile):
        return True

    @classmethod
    def is_powertype_valid(cls, powertype):
        return powertype in cls._supported_powertypes

    # FIXME
    # IT IS NEEDED TO BE CHECKED IF POWER IS VALID
    @classmethod
    def is_power_valid(cls, power):
        return True
