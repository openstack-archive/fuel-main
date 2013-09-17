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
from cliff import lister
from cliff import command
from dhcp_checker import api
from itertools import chain
import json


class BaseCommand(command.Command):
    """Base command for all app
    """
    def get_parser(self, prog_name):
        parser = super(BaseCommand, self).get_parser(prog_name)
        parser.add_argument('--timeout', default=5, type=int,
            help="Provide timeout for each network request")
        parser.add_argument('--repeat', default=2, type=int,
            help="Provide number of repeats for request")
        return parser


class ListDhcpServers(lister.Lister, BaseCommand):
    """Show list of dhcp servers on ethernet interfaces.
    """

    def get_parser(self, prog_name):
        parser = super(ListDhcpServers, self).get_parser(prog_name)
        parser.add_argument(
            '--ifaces', metavar='I', nargs='+',
            help='If no eth provided - will run against all except lo')
        return parser

    def take_action(self, parsed_args):
        res = api.check_dhcp(parsed_args.ifaces,
                            timeout=parsed_args.timeout,
                            repeat=parsed_args.repeat)
        first = res.next()
        columns = first.keys()
        return columns, [first.values()] + [item.values() for item in res]


class ListDhcpAssignment(lister.Lister, BaseCommand):
    """Make dhcp request to servers and receive acknowledgement messages
    """

    def get_parser(self, prog_name):
        parser = super(ListDhcpAssignment, self).get_parser(prog_name)
        parser.add_argument('iface',
                            help='Ethernet interface name')
        parser.add_argument('endpoint',
                            help='Endpoint of server or multicast group')
        parser.add_argument('--range_start', dest='range_start',
                            help='Start of the range')
        parser.add_argument('--range_end', dest='range_end', default=None,
                            help='Start of the range')
        return parser

    def take_action(self, parsed_args):
        res = iter(api.check_dhcp_request(
            parsed_args.iface,
            parsed_args.endpoint,
            parsed_args.range_start,
            parsed_args.range_end, timeout=parsed_args.timeout))
        first = res.next()
        columns = first.keys()
        return columns, [first.values()] + [item.values() for item in res]


class DhcpWithVlansCheck(lister.Lister, BaseCommand):
    """Provide iface with list of vlans to check
    If no vlans created - they will be. After creation they won't be deleted.
    """

    def get_parser(self, prog_name):
        parser = super(DhcpWithVlansCheck, self).get_parser(prog_name)
        parser.add_argument('config',
                             help='Ethernet interface name')
        return parser

    def take_action(self, parsed_args):
        res = api.check_dhcp_with_vlans(json.loads(parsed_args.config),
                            timeout=parsed_args.timeout,
                            repeat=parsed_args.repeat)
        first = res.next()
        columns = first.keys()
        return columns, [first.values()] + [item.values() for item in res]
