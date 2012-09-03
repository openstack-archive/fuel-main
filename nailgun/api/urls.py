#!/usr/bin/env python

import web

from api.handlers import ClusterHandler, ClusterCollectionHandler
from api.handlers import ReleaseHandler, ReleaseCollectionHandler
from api.handlers import NodeHandler, NodeCollectionHandler

urls = (
    r'/releases/?$', 'ReleaseCollectionHandler',
    r'/releases/(?P<release_id>\d+)/?$', 'ReleaseHandler',
    r'/clusters/?$', 'ClusterCollectionHandler',
    r'/clusters/(?P<cluster_id>\d+)/?$', 'ClusterHandler',
    r'/nodes/?$', 'NodeCollectionHandler',
    r'/nodes/(?P<node_id>\d+)/?$', 'NodeHandler',
)

api_app = web.application(urls, locals())
