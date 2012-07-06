from model import Validator
from model.profile import Profile
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
        pass
