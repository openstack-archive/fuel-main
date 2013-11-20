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
DNS = os.environ.get('DNS', '8.8.8.8')

OPENSTACK_RELEASE_CENTOS = 'CentOS 6.4'
OPENSTACK_RELEASE_UBUNTU = 'Ubuntu 12.04'
OPENSTACK_RELEASE_REDHAT = 'RHOS 3.0 for RHEL 6.4'
OPENSTACK_RELEASE = os.environ.get(
    'OPENSTACK_RELEASE', OPENSTACK_RELEASE_CENTOS)

REDHAT_LICENSE_TYPE = os.environ.get('REDHAT_LICENSE_TYPE')
REDHAT_USERNAME = os.environ.get('REDHAT_USERNAME')
REDHAT_PASSWORD = os.environ.get('REDHAT_PASSWORD')
REDHAT_SATELLITE_HOST = os.environ.get('REDHAT_SATELLITE_HOST')
REDHAT_ACTIVATION_KEY = os.environ.get('REDHAT_ACTIVATION_KEY')

DEPLOYMENT_MODE_SIMPLE = "multinode"
DEPLOYMENT_MODE_HA = "ha_compact"

ADMIN_NODE_SETUP_TIMEOUT = os.environ.get("ADMIN_NODE_SETUP_TIMEOUT", 30)

ADMIN_NODE_HARDWARE = {
    "memory": os.environ.get("ADMIN_NODE_MEMORY", 1024),
    "cpu": os.environ.get("ADMIN_NODE_CPU", 1),
    "volume_size": os.environ.get('NODE_VOLUME_SIZE', 50)
}
SLAVE_NODES_HARDWARE = [{
    "memory": os.environ.get("SLAVE_NODE_MEMORY", 1024),
    "cpu": os.environ.get("SLAVE_NODE_CPU", 1),
    "volume_size": os.environ.get('NODE_VOLUME_SIZE', 50)
} for x in range(1, 10)]
SLAVE_NODES_HARDWARE.append({
    "memory": 2048,
    "cpu": 1,
    "volume_size": os.environ.get('NODE_VOLUME_SIZE', 50)
})

ADMIN_FORWARD = os.environ.get('ADMIN_FORWARD', 'nat')
PUBLIC_FORWARD = os.environ.get('PUBLIC_FORWARD', 'nat')


INTERFACE_ORDER = ('admin', 'public', 'management', 'private', 'storage')

FORWARDING = {
    'admin': ADMIN_FORWARD,
    'public': PUBLIC_FORWARD,
    'management': None,
    'private': None,
    'storage': None,
}

DHCP = {
    'admin': False,
    'public': False,
    'management': False,
    'private': False,
    'storage': False
}

INTERFACES = {
    'admin': 'eth0',
    'public': 'eth1',
    'management': 'eth2',
    'private': 'eth3',
    'storage': 'eth4',
}

# May be one of virtio, e1000, pcnet, rtl8139
INTERFACE_MODEL = os.environ.get('INTERFACE_MODEL', 'virtio')

DEFAULT_POOLS = {
    'admin': '10.108.0.0/16:24',
    'public': '10.108.0.0/16:24',
    'management': '10.108.0.0/16:24',
    'private': '10.108.0.0/16:24',
    'storage': '10.108.0.0/16:24',
}

POOLS = {
    'admin': os.environ.get(
        'PUBLIC_POOL',
        DEFAULT_POOLS.get('admin')).split(':'),
    'public': os.environ.get(
        'PUBLIC_POOL',
        DEFAULT_POOLS.get('public')).split(':'),
    'management': os.environ.get(
        'PRIVATE_POOL',
        DEFAULT_POOLS.get('management')).split(':'),
    'private': os.environ.get(
        'INTERNAL_POOL',
        DEFAULT_POOLS.get('private')).split(':'),
    'storage': os.environ.get(
        'NAT_POOL',
        DEFAULT_POOLS.get('storage')).split(':'),
}

NETWORK_MANAGERS = {
    'flat': 'FlatDHCPManager',
    'vlan': 'VlanManager'
}

NEUTRON = 'neutron'

NEUTRON_SEGMENT = {
    'gre': 'gre',
    'vlan': 'vlan'
}

LOGS_DIR = os.environ.get('LOGS_DIR')
USE_ALL_DISKS = os.environ.get('USE_ALL_DISKS', 'true') == 'true'

UPLOAD_MANIFESTS = os.environ.get('UPLOAD_MANIFESTS', 'false') == 'true'
UPLOAD_MANIFESTS_PATH = os.environ.get(
    'UPLOAD_MANIFESTS_PATH', '~/git/fuel/deployment/puppet/')
SITEPP_FOR_UPLOAD = os.environ.get(
    'SITEPP_PATH', '/etc/puppet/modules/osnailyfacter/examples/site.pp')
