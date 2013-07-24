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


import os

ISO_PATH = os.environ.get('ISO_PATH')
EMPTY_SNAPSHOT = os.environ.get('EMPTY_SNAPSHOT', 'empty')

INTERFACE_ORDER = ('internal', 'public', 'private')

PUBLIC_FORWARD = os.environ.get('PUBLIC_FORWARD', None)

FORWARDING = {
    'public': PUBLIC_FORWARD,
    'internal': None,
    'private': None,
}

DHCP = {
    'public': False,
    'internal': False,
    'private': False,
}

INTERFACES = {
    'internal': 'eth0',
    'public': 'eth1',
    'private': 'eth2',
}

DEFAULT_POOLS = {
    'public': '10.108.0.0/16:24',
    'private': '10.108.0.0/16:24',
    'internal': '10.108.0.0/16:24',
}

POOLS = {
    'public': os.environ.get('PUBLIC_POOL',
                             DEFAULT_POOLS.get('public')).split(':'),
    'private': os.environ.get('PRIVATE_POOL',
                              DEFAULT_POOLS.get('private')).split(':'),
    'internal': os.environ.get('INTERNAL_POOL',
                               DEFAULT_POOLS.get('internal')).split(':')
}

NETWORK_MANAGERS = {
    'flat': 'FlatDHCPManager',
    'vlan': 'VlanManager'
}

CLEAN = os.environ.get('CLEAN', 'true') == 'true'
LOGS_DIR = os.environ.get('LOGS_DIR')
