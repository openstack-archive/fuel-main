#!/usr/bin/env python

import web

from api.handlers.cluster import ClusterHandler, ClusterCollectionHandler
from api.handlers.cluster import ClusterChangesHandler, ClusterNetworksHandler
from api.handlers.cluster import ClusterAttributesHandler
from api.handlers.release import ReleaseHandler, ReleaseCollectionHandler
from api.handlers.node import NodeHandler, NodeCollectionHandler
from api.handlers.networks import NetworkCollectionHandler
from api.handlers.tasks import TaskHandler


urls = (
    r'/releases/?$',
    'ReleaseCollectionHandler',
    r'/releases/(?P<release_id>\d+)/?$',
    'ReleaseHandler',
    r'/clusters/?$',
    'ClusterCollectionHandler',
    r'/clusters/(?P<cluster_id>\d+)/?$',
    'ClusterHandler',
    r'/clusters/(?P<cluster_id>\d+)/changes/?$',
    'ClusterChangesHandler',
    r'/clusters/(?P<cluster_id>\d+)/attributes/?$',
    'ClusterAttributesHandler',
    r'/clusters/(?P<cluster_id>\d+)/verify/networks/?$',
    'ClusterNetworksHandler',
    r'/nodes/?$',
    'NodeCollectionHandler',
    r'/nodes/(?P<node_id>\d+)/?$',
    'NodeHandler',
    r'/networks/?$',
    'NetworkCollectionHandler',
    r'/tasks/(?P<node_id>\d+)/?$',
    'TaskHandler',
)

api_app = web.application(urls, locals())
