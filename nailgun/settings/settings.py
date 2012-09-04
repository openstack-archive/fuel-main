# -*- coding: utf-8 -*-

DATABASE_PATH = 'nailgun.sqlite'
DATABASE_ENGINE = 'sqlite:///%s' % DATABASE_PATH

NETWORK_POOLS = {
    'public': ['172.18.0.0/16'],
    'private': ['10.1.0.0/16']
}
