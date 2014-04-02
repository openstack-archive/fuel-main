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
DEPLOYMENT_MODE = os.environ.get("DEPLOYMENT_MODE", DEPLOYMENT_MODE_HA)

ADMIN_NODE_SETUP_TIMEOUT = os.environ.get("ADMIN_NODE_SETUP_TIMEOUT", 30)

HARDWARE = {
    "admin_node_memory": os.environ.get("ADMIN_NODE_MEMORY", 1024),
    "admin_node_cpu": os.environ.get("ADMIN_NODE_CPU", 1),
    "slave_node_cpu": os.environ.get("SLAVE_NODE_CPU", 1),
}
if OPENSTACK_RELEASE_UBUNTU in OPENSTACK_RELEASE:
    slave_mem_default = 2048
else:
    slave_mem_default = 1536
HARDWARE["slave_node_memory"] = int(
    os.environ.get("SLAVE_NODE_MEMORY", slave_mem_default))
NODE_VOLUME_SIZE = os.environ.get('NODE_VOLUME_SIZE', 50)
NODES_COUNT = os.environ.get('NODES_COUNT', 10)

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
UPLOAD_MANIFESTS_PATH = os.environ.get(
    'UPLOAD_MANIFESTS_PATH', '~/git/fuel/deployment/puppet/')
SITEPP_FOR_UPLOAD = os.environ.get(
    'SITEPP_PATH', '/etc/puppet/modules/osnailyfacter/examples/site.pp')


KVM_USE = os.environ.get('KVM_USE', 'false') == 'true'
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'true') == 'true'

#Services tests
SERVTEST_LOCAL_PATH = os.environ.get('SERVTEST_LOCAL_PATH', '/tmp')
SERVTEST_USERNAME = os.environ.get('SERVTEST_USERNAME', 'admin')
SERVTEST_PASSWORD = os.environ.get('SERVTEST_PASSWORD', SERVTEST_USERNAME)
SERVTEST_TENANT = os.environ.get('SERVTEST_TENANT', SERVTEST_USERNAME)
SERVTEST_SAVANNA_SERVER_URL = 'http://savanna-files.mirantis.com'
SERVTEST_SAVANNA_IMAGE = 'savanna-0.3-vanilla-1.2.1-ubuntu-13.04.qcow2'
SERVTEST_SAVANNA_IMAGE_NAME = 'savanna'
SERVTEST_SAVANNA_IMAGE_MD5 = '9ab37ec9a13bb005639331c4275a308d'
SERVTEST_SAVANNA_IMAGE_META = {'_savanna_tag_1.2.1': 'True',
                               '_savanna_tag_vanilla': 'True',
                               '_savanna_username': 'ubuntu'}

SERVTEST_MURANO_SERVER_URL = "http://murano-files.mirantis.com"
SERVTEST_MURANO_IMAGE = "cloud-fedora.qcow2"
SERVTEST_MURANO_IMAGE_MD5 = '6e5e2f149c54b898b3c272f11ae31125'
SERVTEST_MURANO_IMAGE_NAME = 'murano'
SERVTEST_MURANO_IMAGE_META = {
    'murano_image_info': '{"type": "linux", "title": "murano"}'}

SERVTEST_HEAT_SERVER_URL = ("http://fedorapeople.org/groups/"
                            "heat/prebuilt-jeos-images/")
SERVTEST_HEAT_IMAGE = "F17-x86_64-cfntools.qcow2"
SERVTEST_HEAT_IMAGE_NAME = 'F17-x86_64-cfntools'
SERVTEST_HEAT_IMAGE_MD5 = 'afab0f79bac770d61d24b4d0560b5f70'
SERVTEST_HEAT_IMAGE_META = {
    'heat_image_info': '{"type": "fedora", "title": "heat"}'}

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
