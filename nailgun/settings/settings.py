# -*- coding: utf-8 -*-

import posixpath


PROJECT_PATH = posixpath.join(
    posixpath.dirname(posixpath.abspath(__file__)),
    ".."
)

DATABASE_PATH = posixpath.join(PROJECT_PATH, 'nailgun.sqlite')
DATABASE_ENGINE = 'sqlite:///%s' % DATABASE_PATH


STATIC_DIR = posixpath.join(PROJECT_PATH, "static")
TEMPLATE_DIR = posixpath.join(PROJECT_PATH, "static")

NETWORK_POOLS = {
    'public': ['240.0.0.0/24'],  # reserved
    # private nets according to RFC-5735
    'private10': ['10.0.0.0/8'],
    'private172': ['172.16.0.0/12'],
    'private192': ['192.168.0.0/16']
}

NET_EXCLUDE = ['10.20.0.0/24']

VLANS = range(100, 1000)
