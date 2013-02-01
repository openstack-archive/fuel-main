# -*- coding: utf-8 -*-

import json
import traceback

import web

from nailgun.db import orm
from nailgun.logger import logger
from nailgun.notifier import notifier
from nailgun.api.models import NetworkGroup, ClusterChanges
from nailgun.api.handlers.base import JSONHandler


class NetworkCollectionHandler(JSONHandler):
    fields = ('id', 'cluster_id', 'name', 'cidr', 'vlan_start',
              'network_size', 'amount')
    model = NetworkGroup

    def GET(self):
        web.header('Content-Type', 'application/json')
        user_data = web.input(cluster_id=None)
        if user_data.cluster_id:
            nets = orm().query(NetworkGroup).filter_by(
                cluster_id=user_data.cluster_id).all()
        else:
            nets = orm().query(NetworkGroup).all()

        if not nets:
            return web.notfound()

        return json.dumps(
            map(self.render, nets),
            indent=4
        )
