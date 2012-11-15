# -*- coding: utf-8 -*-

import json

import web

from nailgun.notifier import notifier
from nailgun.logger import logger
from nailgun.api.models import Node
from nailgun.api.handlers.base import JSONHandler


class NodeHandler(JSONHandler):
    fields = ('id', 'name', 'info', 'role',
              'status', 'mac', 'fqdn', 'ip', 'manufacturer', 'platform_name',
              'pending_addition', 'pending_deletion', 'os_platform')
    model = Node

    def GET(self, node_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Node)
        node = q.filter(Node.id == node_id).first()
        if not node:
            return web.notfound()

        return json.dumps(
            self.render(node),
            indent=4
        )

    def PUT(self, node_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Node)
        node = q.filter(Node.id == node_id).first()
        if not node:
            return web.notfound()
        # additional validation needed?
        data = Node.validate_update(web.data())
        if not data:
            raise web.badrequest()
        # /additional validation needed?
        for key, value in data.iteritems():
            setattr(node, key, value)
        web.ctx.orm.commit()
        return json.dumps(
            self.render(node),
            indent=4
        )

    def DELETE(self, node_id):
        node = web.ctx.orm.query(Node).filter(
            Node.id == node_id
        ).first()
        if not node:
            return web.notfound()
        web.ctx.orm.delete(node)
        web.ctx.orm.commit()
        raise web.webapi.HTTPError(
            status="204 No Content",
            data=""
        )


class NodeCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        user_data = web.input(cluster_id=None)
        if user_data.cluster_id == '':
            nodes = web.ctx.orm.query(Node).filter_by(
                cluster_id=None).all()
        elif user_data.cluster_id:
            nodes = web.ctx.orm.query(Node).filter_by(
                cluster_id=user_data.cluster_id).all()
        else:
            nodes = web.ctx.orm.query(Node).all()
        return json.dumps(map(
            NodeHandler.render,
            nodes), indent=4)

    def POST(self):
        web.header('Content-Type', 'application/json')
        data = Node.validate(web.data())
        node = Node()
        for key, value in data.iteritems():
            setattr(node, key, value)
        web.ctx.orm.add(node)
        web.ctx.orm.commit()
        ram = round(node.info.get('ram', 0), 1)
        cores = node.info.get('cores', 'unknown')
        notifier.info("New node with %s CPU core(s) "
                      "and %s GB memory is discovered" %
                      (cores, ram))
        raise web.webapi.created(json.dumps(
            NodeHandler.render(node),
            indent=4
        ))

    def PUT(self):
        web.header('Content-Type', 'application/json')
        data = Node.validate_collection_update(web.data())
        q = web.ctx.orm.query(Node)
        nodes_updated = []
        for nd in data:
            if "mac" in nd:
                node = q.filter(Node.mac == nd["mac"]).first()
            else:
                node = q.get(nd["id"])
            for key, value in nd.iteritems():
                setattr(node, key, value)
            nodes_updated.append(node)
            web.ctx.orm.add(node)
        web.ctx.orm.commit()
        return json.dumps(map(
            NodeHandler.render,
            nodes_updated), indent=4)
