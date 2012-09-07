# -*- coding: utf-8 -*-

DATABASE_PATH = 'nailgun.sqlite'
DATABASE_ENGINE = 'sqlite:///%s' % DATABASE_PATH

NETWORK_POOLS = {
    'public': ['240.0.0.0/24'],  # reserved
    # private nets according to RFC-5735
    'private10': ['10.0.0.0/8'],
    'private172': ['172.16.0.0/12'],
    'private192': ['192.168.0.0/16']
}

NET_EXCLUDE = ['10.20.0.0/24']

VLANS = range(100, 1000)
