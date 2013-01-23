# -*- coding: utf-8 -*-

import json

import web

from nailgun.db import orm
from nailgun.logger import logger
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

    def PUT(self):
        web.header('Content-Type', 'application/json')
        new_nets = NetworkGroup.validate_collection_update(web.data())
        if not new_nets:
            raise web.badrequest()

        nets_to_render = []
        for ng in new_nets:
            ng_db = orm().query(NetworkGroup).get(ng['id'])
            if not ng_db:
                raise web.badrequest(
                    message="NetworkGroup with id=%s not found in DB" %
                    ng['id'])
            for key, value in ng.iteritems():
                setattr(ng_db, key, value)
            orm().commit()
            ng_db.create_networks()
            ng_db.cluster.add_pending_changes("networks")
            nets_to_render.append(ng_db)

        return json.dumps(
            map(self.render, nets_to_render),
            indent=4
        )
