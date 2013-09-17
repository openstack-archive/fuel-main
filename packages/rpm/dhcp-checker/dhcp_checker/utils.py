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
import subprocess
import functools
import re


def command_util(*command):
    """object with stderr and stdout
    """
    return subprocess.Popen(command, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)


def _check_vconfig():
    """Check vconfig installed or not
    """
    return not command_util('which', 'vconfig').stderr.read()


def check_network_up(iface):
    state = command_util('ip', 'link', 'show', iface)
    response = re.search(r'state (?P<state>[A-Z]*)', state.stdout.read())
    return response.groupdict()['state'] == 'UP'


def check_iface_exist(iface):
    """Check provided interface exists
    """
    return not command_util("ip","link", "show", iface).stderr.read()


def filtered_ifaces(ifaces):
    for iface in ifaces:
        if not check_iface_exist(iface):
            sys.stderr.write('Iface {0} does not exist.'.format(iface))
        else:
            if not check_network_up(iface):
                sys.stderr.write('Network for iface {0} is down.'.format(iface))
            else:
                yield iface


def pick_ip(range_start, range_end):
    """Given start_range, end_range generate list of ips
    >>> next(pick_ip('192.168.1.10','192.168.1.13'))
    '192.168.1.10'
    """
    split_address = lambda ip_address: \
        [int(item) for item in ip_address.split('.')]
    range_start = split_address(range_start)
    range_end = split_address(range_end)
    i = 0
    # ipv4 subnet cant be longer that 4 items
    while i < 4:
        # 255 - end of subnet
        if not range_start[i] == range_end[i] and range_start[i] < 255:
            yield '.'.join([str(item) for item in range_start])
            range_start[i] += 1
        else:
            i += 1


def format_options(options):
    """Util for serializing dhcp options
    @options = [1,2,3]
    >>> format_options([1, 2, 3])
    '\x01\x02\x03'
    """
    return "".join((chr(item) for item in options))


def _dhcp_options(dhcp_options):
    """Dhcp options returned by scapy is not in usable format
    [('message-type', 2), ('server_id', '192.168.0.5'),
        ('name_server', '192.168.0.1', '192.168.0.2'), 'end']
    """
    for option in dhcp_options:
        if isinstance(option, (tuple, list)):
            header = option[0]
            if len(option[1:]) > 1:
                yield (header, option)
            else:
                yield (header, option[1])


def single_format(func):
    """Manage format of dhcp response
    """
    @functools.wraps(func)
    def formatter(*args, **kwargs):
        iface = args[0]
        ans = func(*args, **kwargs)
        columns = ('iface', 'mac', 'server_ip', 'server_id', 'gateway',
               'dport', 'message', 'yiaddr')
        data = []
        #scapy stores all sequence of requests
        #so ans[0][1] would be response to first request
        for response in ans:
            dhcp_options = dict(_dhcp_options(response[1][DHCP].options))
            results = (
                iface, response[1][Ether].src, response[1][IP].src,
                dhcp_options['server_id'], response[1][BOOTP].giaddr,
                response[1][UDP].sport,
                DHCPTypes[dhcp_options['message-type']],
                response[1][BOOTP].yiaddr)
            data.append(dict(zip(columns, results)))
        return data
    return formatter


def multiproc_map(func):
    # multiproc map could not work with format *args
    @functools.wraps(func)
    def workaround(*args, **kwargs):
        args = args[0] if isinstance(args[0], (tuple, list)) else args
        return func(*args, **kwargs)
    return workaround


def filter_duplicated_results(func):
    # due to network infra on broadcast multiple duplicated results
    # returned. This helper filter them out
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        resp = func(*args, **kwargs)
        return (dict(t) for t in set([tuple(d.items()) for d in resp]))
    return wrapper
