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

from fuelweb_test import logwrap


class Ebtables(object):
    """Ebtables."""  # TODO documentation

    def __init__(self, target_devs, vlans):
        super(Ebtables, self).__init__()
        self.target_devs = target_devs
        self.vlans = vlans

    @logwrap
    def restore_vlans(self):
        for vlan in self.vlans:
            for target_dev in self.target_devs:
                Ebtables.restore_vlan(target_dev, vlan)

    @logwrap
    def restore_first_vlan(self):
        for target_dev in self.target_devs:
            Ebtables.restore_vlan(target_dev, self.vlans[0])

    @logwrap
    def block_first_vlan(self):
        for target_dev in self.target_devs:
            Ebtables.block_vlan(target_dev, self.vlans[0])

    @staticmethod
    @logwrap
    def block_mac(mac):
        return subprocess.check_output(
            ['sudo', 'ebtables', '-t', 'filter', '-A', 'FORWARD', '-s',
             mac, '-j', 'DROP'],
            stderr=subprocess.STDOUT
        )

    @staticmethod
    @logwrap
    def restore_mac(mac):
        return subprocess.call(
            [
                'sudo', 'ebtables', '-t', 'filter',
                '-D', 'FORWARD', '-s', mac, '-j', 'DROP'
            ],
            stderr=subprocess.STDOUT,
        )

    @staticmethod
    @logwrap
    def restore_vlan(target_dev, vlan):
        return subprocess.call(
            [
                'sudo', 'ebtables', '-t', 'broute', '-D', 'BROUTING', '-i',
                target_dev, '-p', '8021Q', '--vlan-id', str(vlan), '-j', 'DROP'
            ],
            stderr=subprocess.STDOUT,
        )

    @staticmethod
    @logwrap
    def block_vlan(target_dev, vlan):
        return subprocess.check_output(
            [
                'sudo', 'ebtables', '-t', 'broute', '-A', 'BROUTING', '-i',
                target_dev, '-p', '8021Q', '--vlan-id', str(vlan), '-j', 'DROP'
            ],
            stderr=subprocess.STDOUT
        )
