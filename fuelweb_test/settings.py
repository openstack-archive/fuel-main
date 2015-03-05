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

# Default timezone for clear logging
TIME_ZONE = 'UTC'

ENV_NAME = os.environ.get("ENV_NAME", "fuel_system_test")

ISO_PATH = os.environ.get('ISO_PATH')
DNS = os.environ.get('DNS', '8.8.8.8')

OPENSTACK_RELEASE_CENTOS = 'centos'
OPENSTACK_RELEASE_UBUNTU = 'ubuntu'
OPENSTACK_RELEASE_REDHAT = 'rhos 3.0 for rhel 6.4'
OPENSTACK_RELEASE = os.environ.get(
    'OPENSTACK_RELEASE', OPENSTACK_RELEASE_CENTOS).lower()

REDHAT_LICENSE_TYPE = os.environ.get('REDHAT_LICENSE_TYPE')
REDHAT_USERNAME = os.environ.get('REDHAT_USERNAME')
REDHAT_PASSWORD = os.environ.get('REDHAT_PASSWORD')
REDHAT_SATELLITE_HOST = os.environ.get('REDHAT_SATELLITE_HOST')
REDHAT_ACTIVATION_KEY = os.environ.get('REDHAT_ACTIVATION_KEY')

DEPLOYMENT_MODE_SIMPLE = "multinode"
DEPLOYMENT_MODE_HA = "ha_compact"
DEPLOYMENT_MODE = os.environ.get("DEPLOYMENT_MODE", DEPLOYMENT_MODE_HA)

ADMIN_NODE_SETUP_TIMEOUT = os.environ.get("ADMIN_NODE_SETUP_TIMEOUT", 30)
PUPPET_TIMEOUT = os.environ.get("PUPPET_TIMEOUT", 6000)

HARDWARE = {
    "admin_node_memory": os.environ.get("ADMIN_NODE_MEMORY", 2048),
    "admin_node_cpu": os.environ.get("ADMIN_NODE_CPU", 2),
    "slave_node_cpu": os.environ.get("SLAVE_NODE_CPU", 1),
}
if OPENSTACK_RELEASE_UBUNTU in OPENSTACK_RELEASE:
    slave_mem_default = 2560
else:
    slave_mem_default = 2048
HARDWARE["slave_node_memory"] = int(
    os.environ.get("SLAVE_NODE_MEMORY", slave_mem_default))
NODE_VOLUME_SIZE = int(os.environ.get('NODE_VOLUME_SIZE', 50))
NODES_COUNT = os.environ.get('NODES_COUNT', 10)

MULTIPLE_NETWORKS = os.environ.get('MULTIPLE_NETWORKS', False) == 'true'

if MULTIPLE_NETWORKS:
    NODEGROUPS = (
        {
            'name': 'default',
            'pools': ['admin', 'public', 'management', 'private',
                      'storage']
        },
        {
            'name': 'group-custom-1',
            'pools': ['admin2', 'public2', 'management2', 'private2',
                      'storage2']
        }
    )
    FORWARD_DEFAULT = os.environ.get('FORWARD_DEFAULT', 'route')
    ADMIN_FORWARD = os.environ.get('ADMIN_FORWARD', 'nat')
    PUBLIC_FORWARD = os.environ.get('PUBLIC_FORWARD', 'nat')
else:
    NODEGROUPS = {}
    FORWARD_DEFAULT = os.environ.get('FORWARD_DEFAULT', None)
    ADMIN_FORWARD = os.environ.get('ADMIN_FORWARD', FORWARD_DEFAULT or 'nat')
    PUBLIC_FORWARD = os.environ.get('PUBLIC_FORWARD', FORWARD_DEFAULT or 'nat')

MGMT_FORWARD = os.environ.get('MGMT_FORWARD', FORWARD_DEFAULT)
PRIVATE_FORWARD = os.environ.get('PRIVATE_FORWARD', FORWARD_DEFAULT)
STORAGE_FORWARD = os.environ.get('STORAGE_FORWARD', FORWARD_DEFAULT)

DEFAULT_INTERFACE_ORDER = 'admin,public,management,private,storage'
INTERFACE_ORDER = os.environ.get('INTERFACE_ORDER',
                                 DEFAULT_INTERFACE_ORDER).split(',')

FORWARDING = {
    'admin': ADMIN_FORWARD,
    'public': PUBLIC_FORWARD,
    'management': MGMT_FORWARD,
    'private': PRIVATE_FORWARD,
    'storage': STORAGE_FORWARD,
}

DHCP = {
    'admin': False,
    'public': False,
    'management': False,
    'private': False,
    'storage': False,
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

POOL_DEFAULT = os.environ.get('POOL_DEFAULT', '10.108.0.0/16:24')
POOL_ADMIN = os.environ.get('POOL_ADMIN', POOL_DEFAULT)
POOL_PUBLIC = os.environ.get('POOL_PUBLIC', POOL_DEFAULT)
POOL_MANAGEMENT = os.environ.get('POOL_MANAGEMENT', POOL_DEFAULT)
POOL_PRIVATE = os.environ.get('POOL_PRIVATE', POOL_DEFAULT)
POOL_STORAGE = os.environ.get('POOL_STORAGE', POOL_DEFAULT)

DEFAULT_POOLS = {
    'admin': POOL_ADMIN,
    'public': POOL_PUBLIC,
    'management': POOL_MANAGEMENT,
    'private': POOL_PRIVATE,
    'storage': POOL_STORAGE,
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

if MULTIPLE_NETWORKS:
    FORWARDING['admin2'] = ADMIN_FORWARD
    FORWARDING['public2'] = PUBLIC_FORWARD
    FORWARDING['management2'] = MGMT_FORWARD
    FORWARDING['private2'] = PRIVATE_FORWARD
    FORWARDING['storage2'] = STORAGE_FORWARD

    DHCP['admin2'] = False
    DHCP['public2'] = False
    DHCP['management2'] = False
    DHCP['private2'] = False
    DHCP['storage2'] = False

    INTERFACES['admin2'] = 'eth5'

    POOL_DEFAULT2 = os.environ.get('POOL_DEFAULT2', '10.108.0.0/16:24')
    POOL_ADMIN2 = os.environ.get('POOL_ADMIN2', POOL_DEFAULT2)
    POOL_PUBLIC2 = os.environ.get('POOL_PUBLIC2', POOL_DEFAULT2)
    POOL_MANAGEMENT2 = os.environ.get('POOL_MANAGEMENT', POOL_DEFAULT2)
    POOL_PRIVATE2 = os.environ.get('POOL_PRIVATE', POOL_DEFAULT2)
    POOL_STORAGE2 = os.environ.get('POOL_STORAGE', POOL_DEFAULT2)

    CUSTOM_POOLS = {
        'admin2': POOL_ADMIN2,
        'public2': POOL_PUBLIC2,
        'management2': POOL_MANAGEMENT2,
        'private2': POOL_PRIVATE2,
        'storage2': POOL_STORAGE2,
    }

    POOLS['admin2'] = os.environ.get(
        'PUBLIC_POOL2',
        CUSTOM_POOLS.get('admin2')).split(':')
    POOLS['public2'] = os.environ.get(
        'PUBLIC_POOL2',
        CUSTOM_POOLS.get('public2')).split(':')
    POOLS['management2'] = os.environ.get(
        'PUBLIC_POOL2',
        CUSTOM_POOLS.get('management2')).split(':')
    POOLS['private2'] = os.environ.get(
        'PUBLIC_POOL2',
        CUSTOM_POOLS.get('private2')).split(':')
    POOLS['storage2'] = os.environ.get(
        'PUBLIC_POOL2',
        CUSTOM_POOLS.get('storage2')).split(':')

    CUSTOM_INTERFACE_ORDER = os.environ.get(
        'CUSTOM_INTERFACE_ORDER',
        'admin2,public2,management2,private2,storage2')
    INTERFACE_ORDER.extend(CUSTOM_INTERFACE_ORDER.split(','))

BONDING = os.environ.get("BONDING", 'false') == 'true'

BONDING_INTERFACES = {
    'admin': ['eth0'],
    'public': ['eth1', 'eth2', 'eth3', 'eth4']
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

LOGS_DIR = os.environ.get('LOGS_DIR', os.getcwd())
USE_ALL_DISKS = os.environ.get('USE_ALL_DISKS', 'true') == 'true'

UPLOAD_MANIFESTS = os.environ.get('UPLOAD_MANIFESTS', 'false') == 'true'
SYNC_DEPL_TASKS = os.environ.get('SYNC_DEPL_TASKS', 'false') == 'true'
UPLOAD_MANIFESTS_PATH = os.environ.get(
    'UPLOAD_MANIFESTS_PATH', '~/git/fuel/deployment/puppet/')
SITEPP_FOR_UPLOAD = os.environ.get(
    'SITEPP_PATH', '/etc/puppet/modules/osnailyfacter/examples/site.pp')

UPLOAD_PATCHSET = os.environ.get('UPLOAD_PATCHSET', 'false') == 'true'
GERRIT_REFSPEC = os.environ.get('GERRIT_REFSPEC')
PATCH_PATH = os.environ.get(
    'PATCH_PATH', '/tmp/fuel-ostf')

KVM_USE = os.environ.get('KVM_USE', 'false') == 'true'
VCENTER_USE = os.environ.get('VCENTER_USE', 'false') == 'true'
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'true') == 'true'

# vCenter tests
VCENTER_IP = os.environ.get('VCENTER_IP')
VCENTER_USERNAME = os.environ.get('VCENTER_USERNAME')
VCENTER_PASSWORD = os.environ.get('VCENTER_PASSWORD')
VCENTER_CLUSTERS = os.environ.get('VCENTER_CLUSTERS')

# Cinder with VMDK backend settings
VC_HOST = os.environ.get('VCENTER_IP')
VC_USER = os.environ.get('VCENTER_USERNAME')
VC_PASSWORD = os.environ.get('VCENTER_PASSWORD')
VC_DATACENTER = os.environ.get('VC_DATACENTER')
VC_DATASTORE = os.environ.get('VC_DATASTORE')
VC_IMAGE_DIR = os.environ.get('VC_IMAGE_DIR')
IMAGES_VCENTER = os.environ.get('IMAGES_VCENTER')

# Services tests
SERVTEST_LOCAL_PATH = os.environ.get('SERVTEST_LOCAL_PATH', '/tmp')
SERVTEST_USERNAME = os.environ.get('SERVTEST_USERNAME', 'admin')
SERVTEST_PASSWORD = os.environ.get('SERVTEST_PASSWORD', SERVTEST_USERNAME)
SERVTEST_TENANT = os.environ.get('SERVTEST_TENANT', SERVTEST_USERNAME)

SERVTEST_SAHARA_VANILLA_2_IMAGE = ('sahara-juno-vanilla-'
                                   '2.4.1-ubuntu-14.04.qcow2')
SERVTEST_SAHARA_VANILLA_2_IMAGE_NAME = 'sahara-juno-vanilla-2.4.1-ubuntu-14.04'
SERVTEST_SAHARA_VANILLA_2_IMAGE_MD5 = 'e32bef0d3bc4b2c906f5499e14f9b377'
SERVTEST_SAHARA_VANILLA_2_IMAGE_META = {'_sahara_tag_2.4.1': 'True',
                                        '_sahara_tag_vanilla': 'True',
                                        '_sahara_username': 'ubuntu'}

SERVTEST_MURANO_IMAGE = "ubuntu_14_04-murano-agent_stable_juno.qcow2"
SERVTEST_MURANO_IMAGE_MD5 = '9f562f3f577dc32698c11a99d3f15070'
SERVTEST_MURANO_IMAGE_NAME = 'murano'
SERVTEST_MURANO_IMAGE_META = {
    'murano_image_info': '{"type": "linux", "title": "murano"}'}

DEFAULT_IMAGES_CENTOS = os.environ.get(
    'DEFAULT_IMAGES_CENTOS',
    '/var/lib/libvirt/images/centos6.4-base.qcow2')

DEFAULT_IMAGES_UBUNTU = os.environ.get(
    'DEFAULT_IMAGES_UBUNTU',
    '/var/lib/libvirt/images/ubuntu-12.04.1-server-amd64-p2.qcow2')

OS_IMAGE = os.environ.get('OS_IMAGE', DEFAULT_IMAGES_CENTOS)

OSTF_TEST_NAME = os.environ.get('OSTF_TEST_NAME',
                                'Check network connectivity'
                                ' from instance via floating IP')
OSTF_TEST_RETRIES_COUNT = int(os.environ.get('OSTF_TEST_RETRIES_COUNT', 50))

# The variable below is only for test:
#       fuelweb_test.tests.tests_strength.test_ostf_repeatable_tests
#       :OstfRepeatableTests.run_ostf_n_times_against_custom_deployment
DEPLOYMENT_NAME = os.environ.get('DEPLOYMENT_NAME')

# Need for iso with docker
TIMEOUT = int(os.environ.get('TIMEOUT', 60))
ATTEMPTS = int(os.environ.get('ATTEMPTS', 5))

#Create snapshots as last step in test-case
MAKE_SNAPSHOT = os.environ.get('MAKE_SNAPSHOT', 'false') == 'true'

NEUTRON_ENABLE = os.environ.get('NEUTRON_ENABLE', 'false') == 'true'
NEUTRON_SEGMENT_TYPE = os.environ.get('NEUTRON_SEGMENT_TYPE',
                                      NEUTRON_SEGMENT["vlan"])

FUEL_SETTINGS_YAML = os.environ.get('FUEL_SETTINGS_YAML',
                                    '/etc/fuel/astute.yaml')
# TarBall data for updates and upgrades

TARBALL_PATH = os.environ.get('TARBALL_PATH')

UPGRADE_FUEL_FROM = os.environ.get('UPGRADE_FUEL_FROM', '6.0.1')
UPGRADE_FUEL_TO = os.environ.get('UPGRADE_FUEL_TO', '6.1')

SNAPSHOT = os.environ.get('SNAPSHOT', '')
# For 5.1.1 we have 2 releases in tarball and should specify what we need
RELEASE_VERSION = os.environ.get('RELEASE_VERSION', "2014.2.2-6.1")

# URL to custom mirror with new OSCI packages wich should be tested,
# for example:
# CentOS: http://osci-obs.vm.mirantis.net:82/centos-fuel-master-20921/centos/
# Ubuntu: http://osci-obs.vm.mirantis.net:82/ubuntu-fuel-master-20921/ubuntu/
CUSTOM_PKGS_MIRROR = os.environ.get('CUSTOM_PKGS_MIRROR', '')

# Location of local mirrors on master node.
LOCAL_MIRROR_UBUNTU = os.environ.get('LOCAL_MIRROR_UBUNTU',
                                     '/var/www/nailgun/ubuntu/x86_64')
LOCAL_MIRROR_CENTOS = os.environ.get('LOCAL_MIRROR_CENTOS',
                                     '/var/www/nailgun/centos/x86_64')

# Release name of local Ubuntu mirror on Fuel master node.
UBUNTU_RELEASE = os.environ.get('UBUNTU_RELEASE', 'precise')

UPDATE_TIMEOUT = os.environ.get('UPDATE_TIMEOUT', 3600)

IMAGE_PROVISIONING = os.environ.get('IMAGE_PROVISIONING', 'false') == 'true'

KEYSTONE_CREDS = {'username': os.environ.get('KEYSTONE_USERNAME', 'admin'),
                  'password': os.environ.get('KEYSTONE_PASSWORD', 'admin'),
                  'tenant_name': os.environ.get('KEYSTONE_TENANT', 'admin')}

SSH_CREDENTIALS = {
    'login': os.environ.get('ENV_FUEL_LOGIN', 'root'),
    'password': os.environ.get('ENV_FUEL_PASSWORD', 'r00tme')}

# Plugin path for plugins tests

GLUSTER_PLUGIN_PATH = os.environ.get('GLUSTER_PLUGIN_PATH')
GLUSTER_CLUSTER_ENDPOINT = os.environ.get('GLUSTER_CLUSTER_ENDPOINT')
EXAMPLE_PLUGIN_PATH = os.environ.get('EXAMPLE_PLUGIN_PATH')
LBAAS_PLUGIN_PATH = os.environ.get('LBAAS_PLUGIN_PATH')

FUEL_STATS_CHECK = os.environ.get('FUEL_STATS_CHECK', 'false') == 'true'
FUEL_STATS_ENABLED = os.environ.get('FUEL_STATS_ENABLED', 'true') == 'true'
FUEL_STATS_SSL = os.environ.get('FUEL_STATS_SSL', 'true') == 'true'
FUEL_STATS_HOST = os.environ.get('FUEL_STATS_HOST',
                                 '172.18.2.169')
FUEL_STATS_PORT = os.environ.get('FUEL_STATS_PORT', '443')

CUSTOM_ENV = os.environ.get('CUSTOM_ENV', 'false') == 'true'
BUILD_IMAGES = os.environ.get('BUILD_IMAGES', 'false') == 'true'

STORE_ASTUTE_YAML = os.environ.get('STORE_ASTUTE_YAML', 'false') == 'true'
