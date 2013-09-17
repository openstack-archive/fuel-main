#!/usr/bin/python
#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import subprocess
import json
import unittest
import time

from dhcp_checker import utils
from dhcp_checker import vlans_utils
from dhcp_checker import api


class TestDhcpServers(unittest.TestCase):

    def test_dhcp_server_on_eth0(self):
        response = api.check_dhcp_on_eth('eth0', 5)
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['server_ip'], '10.0.2.2')

    def test_dhcp_server_on_eth1(self):
        response = api.check_dhcp_on_eth('eth1', 5)
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['server_ip'], '192.168.0.5')

    def test_dhcp_server_on_eth2(self):
        response = api.check_dhcp_on_eth('eth2', 5)
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['server_ip'], '10.10.0.10')


class VlanCreationTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.vlan = vlans_utils.Vlan('eth0', '100')

    def test_vlan_creation(self):
        self.vlan.up()
        time.sleep(5)
        self.assertTrue(self.vlan.state)

    def test_vlan_deletion(self):
        self.assertTrue(self.vlan.state)
        self.vlan.down()
        time.sleep(5)


class VlanCreationWithExistingTestCase(unittest.TestCase):

    def test_check_vlan_down_status(self):
        self.vlan_down = vlans_utils.Vlan('eth0', '110')
        self.vlan_down.create()
        time.sleep(5)
        self.assertEqual(self.vlan_down.state, 'DOWN')
        self.vlan_down.down()
        time.sleep(5)

    def test_repeat_created_vlan(self):
        self.vlan_up = vlans_utils.Vlan('eth0', '112')
        self.vlan_up.up()
        time.sleep(5)
        self.assertEqual(self.vlan_up.state, 'UP')
        self.vlan_up.down()
        time.sleep(5)


class WithVlanDecoratorTestCase(unittest.TestCase):


    def test_with_vlan_enter(self):
        with vlans_utils.VlansContext('eth0', ('101','102','103'), delete=True) as vlan_list:
            time.sleep(5)
            for v in vlan_list:
                self.assertEqual('UP', v.state)
