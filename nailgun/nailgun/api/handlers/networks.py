# -*- coding: utf-8 -*-

import json
import logging

import web

from nailgun.api.models import Network
from nailgun.api.handlers.base import JSONHandler


class NetworkCollectionHandler(JSONHandler):
    fields = ('id', 'cluster_id', 'name', 'cidr', 'gateway', 'vlan_id')
    model = Network

    def GET(self):
        web.header('Content-Type', 'application/json')
        user_data = web.input(cluster_id=None)
        if user_data.cluster_id:
            nets = web.ctx.orm.query(Network).filter(
                Network.cluster_id == user_data.cluster_id).all()
        else:
            nets = web.ctx.orm.query(Network).all()

        if not nets:
            return web.notfound()

        return json.dumps(
            map(self.render, nets),
            indent=4
        )

    def PUT(self):
        web.header('Content-Type', 'application/json')
        new_nets = Network.validate_collection_update(web.data())
        if not new_nets:
            raise web.badrequest()

        nets_to_render = []
        for network in new_nets:
            network_db = web.ctx.orm.query(Network).get(network['id'])
            if not network_db:
                raise web.badrequest(
                    message="Network with id=%s not found in DB" %
                    network['id'])
            # Check if there is no such object
            for key, value in network.iteritems():
                setattr(network_db, key, value)
            nets_to_render.append(network_db)

        web.ctx.orm.commit()
        return json.dumps(
            [n.id for n in nets_to_render],
            indent=4
        )
