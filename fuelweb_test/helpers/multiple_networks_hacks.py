#    Copyright 2014 Mirantis, Inc.
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

# TODO(apanchenko): This file contains hacks (e.g. configuring  of dhcp-server
# or firewall on master node) which are used for testing  multiple cluster
# networks feature:
# https://blueprints.launchpad.net/fuel/+spec/multiple-cluster-networks
# This code should be removed from tests as soon as automatic cobbler
# configuring for non-default admin (PXE) networks is implemented in Fuel

from ipaddr import IPNetwork
from proboscis.asserts import assert_equal

from fuelweb_test import settings
from fuelweb_test import logwrap


@logwrap
def configure_second_admin_cobbler(self):
    dhcp_template = '/etc/cobbler/dnsmasq.template'
    remote = self.get_admin_remote()
    main_admin_ip = str(self.nodes().admin.
                        get_ip_address_by_network_name(self.admin_net))
    second_admin_ip = str(self.nodes().admin.
                          get_ip_address_by_network_name(self.admin_net2))
    second_admin_network = self._get_network(self.admin_net2).split('/')[0]
    second_admin_netmask = self.get_net_mask(self.admin_net2)
    network = IPNetwork('{0}/{1}'.format(second_admin_network,
                                         second_admin_netmask))
    discovery_subnet = [net for net in network.iter_subnets(1)][-1]
    first_discovery_address = str(discovery_subnet.network)
    last_discovery_address = str(discovery_subnet.broadcast - 1)
    new_range = ('dhcp-range=internal2,{0},{1},{2}\\n'
                 'dhcp-option=net:internal2,option:router,{3}\\n'
                 'dhcp-boot=net:internal2,pxelinux.0,boothost,{4}\\n').\
        format(first_discovery_address, last_discovery_address,
               second_admin_netmask, second_admin_ip, main_admin_ip)
    cmd = ("dockerctl shell cobbler sed -r '$a \{0}' -i {1};"
           "dockerctl shell cobbler cobbler sync").format(new_range,
                                                          dhcp_template)
    result = remote.execute(cmd)
    assert_equal(result['exit_code'], 0, ('Failed to add second admin'
                 'network to cobbler: {0}').format(result))


@logwrap
def configure_second_admin_firewall(self, network, netmask):
    remote = self.get_admin_remote()
    # Allow forwarding and correct remote logging
    # for nodes from the second admin network
    rules = [
        ('-t nat -I POSTROUTING -s {0}/{1} -p udp -m udp --dport 514 -m'
         ' comment --comment "rsyslog-udp-514-unmasquerade" -j ACCEPT;').
        format(network, netmask),
        ('-t nat -I POSTROUTING -s {0}/{1} -p tcp -m tcp --dport 514 -m'
         ' comment --comment "rsyslog-tcp-514-unmasquerade" -j ACCEPT;').
        format(network, netmask),
        ('-t nat -I POSTROUTING -s {0}/{1} -o eth+ -m comment --comment '
         '"004 forward_admin_net2" -j MASQUERADE').
        format(network, netmask),
        ('-I FORWARD -i {0} -o docker0 -p tcp -m state --state NEW -m tcp'
         ' --dport 514 -m comment --comment "rsyslog-tcp-514-accept" -j '
         'ACCEPT').format(settings.INTERFACES.get(self.admin_net2)),
        ('-I FORWARD -i {0} -o docker0 -p udp -m state --state NEW -m udp'
         ' --dport 514 -m comment --comment "rsyslog-udp-514-accept" -j '
         'ACCEPT').format(settings.INTERFACES.get(self.admin_net2))
    ]

    for rule in rules:
        cmd = 'iptables {0}'.format(rule)
        result = remote.execute(cmd)
        assert_equal(result['exit_code'], 0,
                     ('Failed to add firewall rule for second admin net'
                      'on master node: {0}, {1}').format(rule, result))
    # Save new firewall configuration
    cmd = 'service iptables save'
    result = remote.execute(cmd)
    assert_equal(result['exit_code'], 0,
                 ('Failed to save firewall configuration on master node:'
                  ' {0}').format(result))


@logwrap
def configure_second_dhcrelay(self):
    remote = self.get_admin_remote()
    second_admin_if = settings.INTERFACES.get(self.admin_net2)
    sed_cmd = "/  interface:/a \  interface: {0}".format(second_admin_if)
    self.fuel_web.modify_python_file(remote, sed_cmd,
                                     settings.FUEL_SETTINGS_YAML)
    cmd = ('supervisorctl restart dhcrelay_monitor; '
           'pgrep -f "[d]hcrelay.*{0}"').format(second_admin_if)
    result = remote.execute(cmd)
    assert_equal(result['exit_code'], 0, ('Failed to start DHCP relay on '
                 'second admin interface: {0}').format(result))
