# -*- coding: utf-8 -*-

import json
import traceback

import web

from nailgun.logger import logger
from nailgun.notifier import notifier
from nailgun.api.models import NetworkGroup, ClusterChanges
from nailgun.api.handlers.base import JSONHandler, content_json


class NetworkCollectionHandler(JSONHandler):
    fields = ('id', 'cluster_id', 'name', 'cidr', 'vlan_start',
              'network_size', 'amount')
    model = NetworkGroup

    @content_json
    def GET(self):
        user_data = web.input(cluster_id=None)
        if user_data.cluster_id:
            nets = self.db.query(NetworkGroup).filter_by(
                cluster_id=user_data.cluster_id).all()
        else:
            nets = self.db.query(NetworkGroup).all()

        if not nets:
            return web.notfound()

        return map(self.render, nets)
