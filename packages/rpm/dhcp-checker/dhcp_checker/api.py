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

from scapy.all import *
import itertools
import multiprocessing
import functools
import subprocess
from dhcp_checker import utils
from dhcp_checker import vlans_utils


@utils.multiproc_map
@utils.single_format
def check_dhcp_on_eth(iface, timeout):
    """Check if there is roque dhcp server in network on given iface
        @iface - name of the ethernet interface
        @timeout - scapy timeout for waiting on response
    >>> check_dhcp_on_eth('eth1')
    """

    conf.iface = iface

    conf.checkIPaddr = False
    dhcp_options = [("message-type", "discover"),
                    ("param_req_list", utils.format_options([1, 2, 3, 4, 5, 6,
                        11, 12, 13, 15, 16, 17, 18, 22, 23,
                        28, 40, 41, 42, 43, 50, 51, 54, 58, 59, 60, 66, 67])),
                    "end"]

    fam, hw = get_if_raw_hwaddr(iface)
    dhcp_discover = (
        Ether(src=hw, dst="ff:ff:ff:ff:ff:ff") /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(chaddr=hw) /
        DHCP(options=dhcp_options))
    ans, unans = srp(dhcp_discover, multi=True,
                     nofilter=1, timeout=timeout, verbose=0)
    return ans


@utils.filter_duplicated_results
def check_dhcp(ifaces, timeout=5, repeat=2):
    """Given list of ifaces. Process them in separate processes
    @ifaces - lsit of ifaces
    @timeout - timeout for scapy to wait for response
    @repeat - number of packets sended
    >>> check_dhcp(['eth1', 'eth2'])
    """
    ifaces_filtered = list(utils.filtered_ifaces(ifaces))
    if not ifaces_filtered:
        raise EnvironmentError("No valid interfaces provided.")
    pool = multiprocessing.Pool(len(ifaces_filtered)*repeat)
    return itertools.chain(*pool.map(check_dhcp_on_eth,
        ((iface, timeout) for iface in ifaces_filtered*repeat)))


def check_dhcp_with_vlans(config, timeout=5, repeat=2):
    """
    @config - {'eth0': (100, 101), 'eth1': (100, 102)}
    @ifaces - string : eth0, eth1
    @vlans - iterable (100, 101, 102)
    """
    with vlans_utils.VlansActor(config) as vifaces:
        return check_dhcp(list(vifaces), timeout=timeout, repeat=repeat)


@utils.single_format
def check_dhcp_request(iface, server, range_start, range_end, timeout=5):
    """Provide interface, server endpoint and pool of ip adresses
        Should be used after offer received
        >>> check_dhcp_request('eth1','10.10.0.5','10.10.0.10','10.10.0.15')
    """

    conf.iface = iface

    conf.checkIPaddr = False

    fam, hw = get_if_raw_hwaddr(iface)

    ip_address = next(utils.pick_ip(range_start, range_end))

    # note lxc dhcp server does not respond to unicast
    dhcp_request = (Ether(src=hw, dst="ff:ff:ff:ff:ff:ff") /
                    IP(src="0.0.0.0", dst="255.255.255.255") /
                    UDP(sport=68, dport=67) /
                    BOOTP(chaddr=hw) /
                    DHCP(options=[("message-type", "request"),
                                  ("server_id", server),
                                  ("requested_addr", ip_address), "end"]))
    ans, unans = srp(dhcp_request, nofilter=1, multi=True,
                     timeout=timeout, verbose=0)
    return ans
