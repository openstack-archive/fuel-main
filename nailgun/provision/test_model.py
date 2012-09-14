# -*- coding: utf-8 -*-

from unittest import TestCase

from model import Validator
from model.profile import Profile
from model.node import Node
from model.power import Power


class TestValidator(TestCase):
    def setUp(self):
        self.mac = "c8:0a:a9:a6:ff:28"
        self.platform = ("ubuntu", "precise", "x86_64")
        self.os = "ubuntu"
        self.osversion = "precise"
        self.arch = "x86_64"

    def test_is_mac_valid(self):
        self.assertTrue(Validator.is_mac_valid(self.mac))

    def test_is_platform_valid(self):
        self.assertTrue(Validator.is_platform_valid(
            self.platform[0],
            self.platform[1],
            self.platform[2]
        ))

    def test_is_os_valid(self):
        self.assertTrue(Validator.is_os_valid(self.os))

    def test_is_osversion_valid(self):
        self.assertTrue(Validator.is_osversion_valid(self.osversion))

    def test_is_arch_valid(self):
        self.assertTrue(Validator.is_arch_valid(self.arch))


class TestProfile(TestCase):
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
        self.assertEqual(self.profile.arch, self.arch)

    def test_os(self):
        self.profile.os = self.os
        self.assertEqual(self.profile.os, self.os)

    def test_osversion(self):
        self.profile.osversion = self.osversion
        self.assertEqual(self.profile.osversion, self.osversion)

    def test_kernel(self):
        self.profile.kernel = self.kernel
        self.assertEqual(self.profile.kernel, self.kernel)

    def test_initrd(self):
        self.profile.initrd = self.initrd
        self.assertEqual(self.profile.initrd, self.initrd)

    def test_seed(self):
        self.profile.seed = self.seed
        self.assertEqual(self.profile.seed, self.seed)

    def test_kopts(self):
        self.profile.kopts = self.kopts
        self.assertEqual(self.profile.kopts, self.kopts)


class TestNode(TestCase):
    def setUp(self):
        self.node = Node('node')
        self.mac = "c8:0a:a9:a6:ff:28"
        self.profile = Profile('profile')
        self.kopts = "kopts"
        self.pxe = True
        self.power = Power('ssh')

    def test_mac(self):
        self.node.mac = self.mac
        self.assertEqual(self.node.mac, self.mac)

    def test_profile(self):
        self.node.profile = self.profile
        self.assertEqual(self.node.profile, self.profile)

    def test_kopts(self):
        self.node.kopts = self.kopts
        self.assertEqual(self.node.kopts, self.kopts)

    def test_pxe(self):
        self.node.pxe = self.pxe
        self.assertEqual(self.node.pxe, self.pxe)

    def test_power(self):
        self.node.power = self.power
        self.assertEqual(self.node.power, self.power)


class TestPower(TestCase):
    def setUp(self):
        self.power = Power('ssh')
        self.power_user = "user"
        self.power_pass = "pass"
        self.power_address = "localhost"
        self.power_id = "localhost"

    def test_power_user(self):
        self.power.power_user = self.power_user
        self.assertEqual(self.power.power_user, self.power_user)

    def test_power_pass(self):
        self.power.power_pass = self.power_pass
        self.assertEqual(self.power.power_pass, self.power_pass)

    def test_power_address(self):
        self.power.power_address = self.power_address
        self.assertEqual(self.power.power_address, self.power_address)

    def test_power_id(self):
        self.power.power_id = self.power_id
        self.assertEqual(self.power.power_id, self.power_id)
