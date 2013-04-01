import os

ISO = os.environ.get('ISO')
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

CLEAN = os.environ.get('CLEAN', 'true') == 'true'
LOGS_DIR = os.environ.get('LOGS_DIR')
