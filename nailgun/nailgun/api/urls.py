# -*- coding: utf-8 -*-

import web

from nailgun.api.handlers.cluster import ClusterHandler
from nailgun.api.handlers.cluster import ClusterCollectionHandler
from nailgun.api.handlers.cluster import ClusterChangesHandler
from nailgun.api.handlers.cluster import ClusterNetworksHandler
from nailgun.api.handlers.cluster import ClusterAttributesHandler

from nailgun.api.handlers.release import ReleaseHandler
from nailgun.api.handlers.release import ReleaseCollectionHandler

from nailgun.api.handlers.node import NodeHandler
from nailgun.api.handlers.node import NodeCollectionHandler

from nailgun.api.handlers.networks import NetworkCollectionHandler
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.api.handlers.tasks import TaskCollectionHandler

from nailgun.api.handlers.notifications import NotificationHandler
from nailgun.api.handlers.notifications import NotificationCollectionHandler

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
    r'/tasks/?$',
    'TaskCollectionHandler',
    r'/tasks/(?P<task_id>\d+)/?$',
    'TaskHandler',
    r'/notifications/?$',
    'NotificationCollectionHandler',
    r'/notifications/(?P<notification_id>\d+)/?$',
    'NotificationHandler',
)

api_app = web.application(urls, locals())
