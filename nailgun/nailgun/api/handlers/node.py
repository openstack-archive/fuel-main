# -*- coding: utf-8 -*-

import json
from datetime import datetime

import web

from nailgun.notifier import notifier
from nailgun.logger import logger
<<<<<<< HEAD
from nailgun.api.models import Node
from nailgun.api.validators import NodeValidator
from nailgun.network.manager import NetworkManager
from nailgun.api.handlers.base import JSONHandler, content_json
=======
from nailgun.api.models import Node, NodeAttributes
from nailgun.api.handlers.base import JSONHandler
>>>>>>> initial volume backend


class NodeHandler(JSONHandler):
    fields = ('id', 'name', 'meta', 'role', 'progress',
              'status', 'mac', 'fqdn', 'ip', 'manufacturer', 'platform_name',
              'pending_addition', 'pending_deletion', 'os_platform',
              'error_type', 'online', 'cluster')
    model = Node
    validator = NodeValidator

    @classmethod
    def render(cls, instance, fields=None):
        json_data = JSONHandler.render(instance, fields=cls.fields)
        network_manager = NetworkManager()
        json_data['network_data'] = network_manager.get_node_networks(
            instance.id
        )
        return json_data

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        return self.render(node)

    @content_json
    def PUT(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        data = self.validator.validate_update(web.data())
        for key, value in data.iteritems():
            setattr(node, key, value)
        self.db.commit()
        return self.render(node)

    def DELETE(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        self.db.delete(node)
        self.db.commit()
        raise web.webapi.HTTPError(
            status="204 No Content",
            data=""
        )


class NodeCollectionHandler(JSONHandler):

    validator = NodeValidator

    @content_json
    def GET(self):
        user_data = web.input(cluster_id=None)
        if user_data.cluster_id == '':
            nodes = self.db.query(Node).filter_by(
                cluster_id=None).all()
        elif user_data.cluster_id:
            nodes = self.db.query(Node).filter_by(
                cluster_id=user_data.cluster_id).all()
        else:
            nodes = self.db.query(Node).all()
        return map(NodeHandler.render, nodes)

    @content_json
    def POST(self):
        data = self.validator.validate(web.data())
        node = Node()
        for key, value in data.iteritems():
            setattr(node, key, value)
        node.name = "Untitled (%s)" % data['mac'][-5:]
        node.timestamp = datetime.now()
        self.db.add(node)
        self.db.commit()
        try:
            ram = str(round(float(
                node.meta['memory']['total']) / 1073741824, 1))
        except (KeyError, TypeError, ValueError):
            ram = "unknown"
        cores = str(node.meta.get('cpu', {}).get('total', "unknown"))
        notifier.notify("discover",
                        "New node with %s CPU core(s) "
                        "and %s GB memory is discovered" %
                        (cores, ram), node_id=node.id)
        raise web.webapi.created(json.dumps(
            NodeHandler.render(node),
            indent=4
        ))

    @content_json
    def PUT(self):
        data = self.validator.validate_collection_update(web.data())
        q = self.db.query(Node)
        nodes_updated = []
        for nd in data:
            is_agent = nd.pop("is_agent") if "is_agent" in nd else False
            node = None
            if "mac" in nd:
                node = q.filter_by(mac=nd["mac"]).first() \
                    or self.validator.validate_existent_node_mac(nd)
            else:
                node = q.get(nd["id"])
            for key, value in nd.iteritems():
                if is_agent and (key, value) == ("status", "discover") \
                        and node.status == "provisioning":
                    # We don't update provisioning back to discover
                    logger.debug(
                        "Node is already provisioning - "
                        "status not updated by agent"
                    )
                    continue
                setattr(node, key, value)
            if is_agent:
                node.timestamp = datetime.now()
                if not node.online:
                    node.online = True
                    msg = u"Node '{0}' is back online".format(
                        node.name or node.mac
                    )
                    logger.info(msg)
                    notifier.notify(
                        "discover",
                        msg,
                        node_id=node.id
                    )
            nodes_updated.append(node)
<<<<<<< HEAD
            self.db.add(node)
            self.db.commit()
        return map(NodeHandler.render, nodes_updated)
=======
            orm().add(node)
        orm().commit()
        return json.dumps(map(
            NodeHandler.render,
            nodes_updated), indent=4)


class NodeAttributesHandler(JSONHandler):
    fields = ('node_id', 'volumes')

    def GET(self, node_id):
        web.header('Content-Type', 'application/json')
        node_attrs = orm().query(Node).get(node_id).attributes
        if not node_attrs:
            return web.notfound()
        return json.dumps(
            self.render(node_attrs),
            indent=4
        )

    def PUT(self):
        web.header('Content-Type', 'application/json')
        node_attrs = orm().query(Node).get(node_id).attributes
        if not node_attrs:
            return web.notfound()
        for key, value in web.data().iteritems():
            setattr(node_attrs, key, value)
        orm().commit()
        return json.dumps(
            self.render(node_attrs),
            indent=4
        )


class NodeAttributesByNameHandler(JSONHandler):

    def GET(self, node_id, attr_name):
        web.header('Content-Type', 'application/json')
        node_attrs = orm().query(Node).get(node_id).attributes
        if not hasattr(node_attrs, attr_name):
            raise web.notfound()
        return json.dumps(
            getattr(node_attrs, attr_name),
            indent=4
        )
>>>>>>> initial volume backend
