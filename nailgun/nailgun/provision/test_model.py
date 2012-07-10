from model import Validator
from model.profile import Profile
from model.node import Node
from model.power import Power
from nose.tools import eq_


class TestValidator:
    def setUp(self):
        self.mac = "c8:0a:a9:a6:ff:28"
        self.platform = ("ubuntu", "precise", "x86_64")
        self.os = "ubuntu"
        self.osversion = "precise"
        self.arch = "x86_64"

    def test_is_mac_valid(self):
        assert  Validator.is_mac_valid(self.mac)

    def test_is_platform_valid(self):
        assert Validator.is_platform_valid(
            self.platform[0],
            self.platform[1],
            self.platform[2]
        )

    def test_is_os_valid(self):
        assert Validator.is_os_valid(self.os)

    def test_is_osversion_valid(self):
        assert Validator.is_osversion_valid(self.osversion)

    def test_is_arch_valid(self):
        assert Validator.is_arch_valid(self.arch)


class TestProfile:
    def setUp(self):
        self.profile = Profile('profile')
        self.arch = "x86_64"
        self.os = "ubuntu"
        self.osversion = "precise"
        self.kernel = "kernel"
        self.initrd = "initrd"
        self.seed = "seed"
        self.kopts = "kopts"

    def test_arch(self):
        self.profile.arch = self.arch
        eq_(self.profile.arch, self.arch)

    def test_os(self):
        self.profile.os = self.os
        eq_(self.profile.os, self.os)

    def test_osversion(self):
        self.profile.osversion = self.osversion
        eq_(self.profile.osversion, self.osversion)

    def test_kernel(self):
        self.profile.kernel = self.kernel
        eq_(self.profile.kernel, self.kernel)

    def test_initrd(self):
        self.profile.initrd = self.initrd
        eq_(self.profile.initrd, self.initrd)

    def test_seed(self):
        self.profile.seed = self.seed
        eq_(self.profile.seed, self.seed)

    def test_kopts(self):
        self.profile.kopts = self.kopts
        eq_(self.profile.kopts, self.kopts)


class TestNode:
    def setUp(self):
        self.node = Node('node')
        self.mac = "c8:0a:a9:a6:ff:28"
        self.profile = Profile('profile')
        self.kopts = "kopts"
        self.pxe = True
        self.power = Power('ssh')

    def test_mac(self):
        self.node.mac = self.mac
        eq_(self.node.mac, self.mac)

    def test_profile(self):
        self.node.profile = self.profile
        eq_(self.node.profile, self.profile)

    def test_kopts(self):
        self.node.kopts = self.kopts
        eq_(self.node.kopts, self.kopts)

    def test_pxe(self):
        self.node.pxe = self.pxe
        eq_(self.node.pxe, self.pxe)

    def test_power(self):
        self.node.power = self.power
        eq_(self.node.power, self.power)


class TestPower:
    def setUp(self):
        self.power = Power('ssh')
        self.power_user = "user"
        self.power_pass = "pass"
        self.power_address = "localhost"
        self.power_id = "localhost"

    def test_power_user(self):
        self.power.power_user = self.power_user
        eq_(self.power.power_user, self.power_user)

    def test_power_pass(self):
        self.power.power_pass = self.power_pass
        eq_(self.power.power_pass, self.power_pass)

    def test_power_address(self):
        self.power.power_address = self.power_address
        eq_(self.power.power_address, self.power_address)

    def test_power_id(self):
        self.power.power_id = self.power_id
        eq_(self.power.power_id, self.power_id)
