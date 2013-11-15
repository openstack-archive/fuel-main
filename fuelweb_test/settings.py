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

ENV_NAME = os.environ.get("ENV_NAME", "fuel_system_test")

ISO_PATH = os.environ.get('ISO_PATH')

OPENSTACK_RELEASE_CENTOS = 'Grizzly on CentOS 6.4'
OPENSTACK_RELEASE_UBUNTU = 'Grizzly on Ubuntu 12.04'
OPENSTACK_RELEASE_REDHAT = 'RHOS 3.0 for RHEL 6.4'
OPENSTACK_RELEASE = os.environ.get(
    'OPENSTACK_RELEASE', OPENSTACK_RELEASE_CENTOS)

REDHAT_LICENSE_TYPE = os.environ.get('REDHAT_LICENSE_TYPE')
REDHAT_USERNAME = os.environ.get('REDHAT_USERNAME')
REDHAT_PASSWORD = os.environ.get('REDHAT_PASSWORD')
REDHAT_SATELLITE_HOST = os.environ.get('REDHAT_SATELLITE_HOST')
REDHAT_ACTIVATION_KEY = os.environ.get('REDHAT_ACTIVATION_KEY')

INTERFACE_ORDER = ('internal', 'public', 'private', 'nat')

PUBLIC_FORWARD = os.environ.get('PUBLIC_FORWARD', None)
NAT_FORWARD = os.environ.get('NAT_FORWARD', 'nat')

ADMIN_NODE_SETUP_TIMEOUT = os.environ.get("ADMIN_NODE_SETUP_TIMEOUT", 30)

HARDWARE = {
    "admin_node_memory": os.environ.get("ADMIN_NODE_MEMORY", 1024),
    "admin_node_cpu": os.environ.get("ADMIN_NODE_CPU", 1),
    "slave_node_memory": os.environ.get("SLAVE_NODE_MEMORY", 1024),
    "slave_node_cpu": os.environ.get("SLAVE_NODE_CPU", 1),
}

FORWARDING = {
    'public': PUBLIC_FORWARD,
    'internal': None,
    'private': None,
    'nat': NAT_FORWARD,
}

DHCP = {
    'public': False,
    'internal': False,
    'private': False,
    'nat': False,
}

INTERFACES = {
    'internal': 'eth0',
    'public': 'eth1',
    'private': 'eth2',
    'nat': 'eth3',
}

DEFAULT_POOLS = {
    'public': '10.108.0.0/16:24',
    'private': '10.108.0.0/16:24',
    'internal': '10.108.0.0/16:24',
    'nat': '10.108.0.0/16:24',
}

POOLS = {
    'public': os.environ.get('PUBLIC_POOL',
                             DEFAULT_POOLS.get('public')).split(':'),
    'private': os.environ.get('PRIVATE_POOL',
                              DEFAULT_POOLS.get('private')).split(':'),
    'internal': os.environ.get('INTERNAL_POOL',
                               DEFAULT_POOLS.get('internal')).split(':'),
    'nat': os.environ.get('NAT_POOL',
                          DEFAULT_POOLS.get('nat')).split(':'),
}

NETWORK_MANAGERS = {
    'flat': 'FlatDHCPManager',
    'vlan': 'VlanManager'
}

LOGS_DIR = os.environ.get('LOGS_DIR')
USE_ALL_DISKS = os.environ.get('USE_ALL_DISKS', 'true') == 'true'

UPLOAD_MANIFESTS = os.environ.get('UPLOAD_MANIFESTS', 'false') == 'true'
UPLOAD_MANIFESTS_PATH = os.environ.get(
    'UPLOAD_MANIFESTS_PATH', '~/git/fuel/deployment/puppet/')
SITEPP_FOR_UPLOAD = os.environ.get(
    'SITEPP_PATH', '/etc/puppet/modules/osnailyfacter/examples/site.pp')
