# -*- coding: utf-8 -*-

import json
import traceback
from datetime import datetime

import web

from nailgun.notifier import notifier
from nailgun.logger import logger
from nailgun.api.models import Node
from nailgun.api.models import Network
from nailgun.api.models import NetworkAssignment
from nailgun.api.models import NodeNICInterface
from nailgun.network.topology import TopoChecker, NICUtils
from nailgun.api.validators import NodeValidator, NetAssignmentValidator
from nailgun.api.validators import NodeAttributesValidator
from nailgun.network.manager import NetworkManager
from nailgun.volumes.manager import VolumeManager
from nailgun.api.models import Node, NodeAttributes
from nailgun.api.handlers.base import JSONHandler, content_json


class NodeHandler(JSONHandler, NICUtils):
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
        if not node.attributes:
            node.attributes = NodeAttributes(node_id=node.id)
        data = self.validator.validate_update(web.data())
        for key, value in data.iteritems():
            setattr(node, key, value)
            if key == 'cluster_id':
                if key:
                    self.allow_network_assignment_to_all_interfaces(node)
                    self.assign_networks_to_main_interface(node)
                else:
                    self.clear_assigned_networks(node)
                    self.clear_all_allowed_networks(node)
        if not node.status in ('provisioning', 'deploying') \
                and "role" in data or "cluster_id" in data:
            try:
                node.attributes.volumes = \
                    node.volume_manager.gen_volumes_info()
            except Exception as exc:
                msg = (
                    u"Failed to generate volumes "
                    "info for node '{0}': '{1}'"
                ).format(
                    node.name or data.get("mac") or data.get("id"),
                    str(exc) or "see logs for details"
                )
                logger.warning(traceback.format_exc())
                notifier.notify("error", msg, node_id=node.id)
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


class NodeCollectionHandler(JSONHandler, NICUtils):

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
        node.attributes = NodeAttributes()
        try:
            node.attributes.volumes = node.volume_manager.gen_volumes_info()
            if node.cluster:
                node.cluster.add_pending_changes(
                    "disks",
                    node_id=node.id
                )
        except Exception as exc:
            msg = (
                "Failed to generate volumes "
                "info for node '{0}': '{1}'"
            ).format(
                node.name or data.get("mac") or data.get("id"),
                str(exc) or "see logs for details"
            )
            logger.warning(traceback.format_exc())
            notifier.notify("error", msg, node_id=node.id)
        self.db.add(node)
        self.db.commit()

        # Add interfaces for node from 'meta'.
        if node.meta and node.meta.get('interfaces'):
            nics = self.get_nics_from_meta(node)
            map(self.db.add, nics)
            self.db.commit()
        if node.cluster_id:
            self.allow_network_assignment_to_all_interfaces(node)
            self.assign_networks_to_main_interface(node)
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
            if nd.get("cluster_id") is None and node.cluster:
                node.cluster.clear_pending_changes(node_id=node.id)
            old_cluster_id = node.cluster_id
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
            if not node.attributes:
                node.attributes = NodeAttributes()
                self.db.commit()
            if not node.status in ('provisioning', 'deploying'):
                variants = (
                    not node.attributes.volumes,
                    "disks" in node.meta and
                    len(node.meta["disks"]) != len(
                        filter(
                            lambda d: d["type"] == "disk",
                            node.attributes.volumes
                        )
                    ),
                    "role" in nd,
                    "cluster_id" in nd
                )
                if any(variants):
                    try:
                        node.attributes.volumes = \
                            node.volume_manager.gen_volumes_info()
                        if node.cluster:
                            node.cluster.add_pending_changes(
                                "disks",
                                node_id=node.id
                            )
                    except Exception as exc:
                        msg = (
                            "Failed to generate volumes "
                            "info for node '{0}': '{1}'"
                        ).format(
                            node.name or data.get("mac") or data.get("id"),
                            str(exc) or "see logs for details"
                        )
                        logger.warning(traceback.format_exc())
                        notifier.notify("error", msg, node_id=node.id)

                self.db.commit()
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
                # Update node's NICs.
                if node.meta and 'interfaces' in node.meta:
                    db_nics = list(node.interfaces)
                    nics = self.get_nics_from_meta(node)
                    for nic in nics:
                        db_nic = filter(lambda i: i.mac == nic.mac, db_nics)
                        if not db_nic:
                            self.db.add(nic)
                            continue
                        db_nic = db_nic[0]
                        for key in ('name', 'current_speed', 'max_speed'):
                            setattr(db_nic, key, getattr(nic, key))
                        db_nics.remove(db_nic)
                    map(self.db.delete, db_nics)
            nodes_updated.append(node)
            self.db.add(node)
            self.db.commit()
            if 'cluster_id' in nd and nd['cluster_id'] != old_cluster_id:
                if old_cluster_id:
                    self.clear_assigned_networks(node)
                    self.clear_all_allowed_networks(node)
                if nd['cluster_id']:
                    self.allow_network_assignment_to_all_interfaces(node)
                    self.assign_networks_to_main_interface(node)
                self.db.commit()
        return map(NodeHandler.render, nodes_updated)


class NodeAttributesHandler(JSONHandler):
    fields = ('node_id', 'volumes')

    validator = NodeAttributesValidator

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        node_attrs = node.attributes
        if not node_attrs:
            return web.notfound()
        return self.render(node_attrs)

    @content_json
    def PUT(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        # NO serious data validation yet
        data = self.validator.validate_json(web.data())
        if "volumes" in data:
            if node.cluster:
                node.cluster.add_pending_changes(
                    "disks",
                    node_id=node.id
                )
        node_attrs = node.attributes
        if not node_attrs:
            return web.notfound()
        for key, value in data.iteritems():
            setattr(node_attrs, key, value)
        self.db.commit()
        return self.render(node_attrs)


class NodeAttributesDefaultsHandler(JSONHandler):
    fields = ('node_id', 'volumes')

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        if not node.attributes:
            return web.notfound()
        attr_params = web.input()
        json_data = NodeAttributesHandler.render(
            NodeAttributes(
                node_id=node.id,
                volumes=node.volume_manager.gen_volumes_info()
            )
        )
        if hasattr(attr_params, "type"):
            json_data["volumes"] = filter(
                lambda a: a["type"] == attr_params.type,
                json_data["volumes"]
            )
        return json_data

    @content_json
    def PUT(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        if not node.attributes:
            return web.notfound()
        node.attributes = NodeAttributes()
        node.attributes.volumes = node.volume_manager.gen_volumes_info()
        if node.cluster:
            node.cluster.add_pending_changes(
                "disks",
                node_id=node.id
            )
        self.db.commit()
        return self.render(node.attributes)


class NodeAttributesByNameDefaultsHandler(JSONHandler):

    @content_json
    def GET(self, node_id, attr_name):
        attr_params = web.input()
        node = self.get_object_or_404(Node, node_id)
        if attr_name == "volumes":
            attr = node.volume_manager.gen_volumes_info()
        else:
            raise web.notfound()
        if hasattr(attr_params, "type"):
            attr = filter(lambda a: a["type"] == attr_params.type, attr)
        return attr


class NodeAttributesByNameHandler(JSONHandler):

    validator = NodeAttributesValidator

    @content_json
    def GET(self, node_id, attr_name):
        attr_params = web.input()
        node = self.get_object_or_404(Node, node_id)
        node_attrs = node.attributes
        if not node_attrs or not hasattr(node_attrs, attr_name):
            raise web.notfound()
        attr = getattr(node_attrs, attr_name)
        if hasattr(attr_params, "type"):
            attr = filter(lambda a: a["type"] == attr_params.type, attr)
        return attr

    @content_json
    def PUT(self, node_id, attr_name):
        node = self.get_object_or_404(Node, node_id)
        # NO serious data validation yet
        data = NodeAttributesValidator.validate_json(web.data())
        attr_params = web.input()
        node_attrs = node.attributes
        if not node_attrs or not hasattr(node_attrs, attr_name):
            raise web.notfound()

        if node.cluster:
            node.cluster.add_pending_changes(
                "disks",
                node_id=node.id
            )

        attr = getattr(node_attrs, attr_name)
        if hasattr(attr_params, "type"):
            if isinstance(attr, list):
                setattr(
                    node_attrs,
                    attr_name,
                    filter(
                        lambda a: a["type"] != attr_params.type,
                        attr
                    )
                )
                attr = getattr(node_attrs, attr_name)
                for a in data:
                    if a in attr:
                        continue
                    attr.append(a)

                attr = filter(
                    lambda a: a["type"] == attr_params.type,
                    getattr(node_attrs, attr_name)
                )
        else:
            setattr(node_attrs, attr_name, data)
            attr = getattr(node_attrs, attr_name)
        return attr


class NodeNICsHandler(JSONHandler, NICUtils):
    fields = (
        'id', (
            'interfaces',
            'id',
            'mac',
            'name',
            'current_speed',
            'max_speed',
            ('assigned_networks', 'id', 'name'),
            ('allowed_networks', 'id', 'name')
        )
    )

    model = NodeNICInterface
    validator = NetAssignmentValidator

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        return self.render(node)['interfaces']

    # @content_json
    # def PUT(self, node_id):
    #     data = self.validator.validate_json(web.data())
    #     node = {'id': node_id, 'interfaces': data}
    #     data = self.validator.validate(node)
    #     self.update_attributes(node)


class NodeCollectionNICsHandler(NodeNICsHandler):

    validator = NetAssignmentValidator

        # @content_json
        # def GET(self):
        #     user_data = web.input(cluster_id=None)
        #     if user_data.cluster_id == '':
        #         nodes = self.db.query(Node).filter_by(
        #             cluster_id=None).all()
        #     elif user_data.cluster_id:
        #         nodes = self.db.query(Node).filter_by(
        #             cluster_id=user_data.cluster_id).all()
        #     else:
        #         nodes = self.db.query(Node).all()
        #     return map(self.render, nodes)

    @content_json
    def PUT(self):
        data = self.validator.validate_collection_structure(web.data())
        nodes = self.update_collection_attributes(data)
        return map(self.render, nodes)


class NodeNICsDefaultHandler(JSONHandler, NICUtils):
    fields = (
        'id', (
            'interfaces',
            'id',
            'mac',
            'name',
            'current_speed',
            'max_speed',
            ('assigned_networks', 'id', 'name'),
            ('allowed_networks', 'id', 'name')
        )
    )

    validator = NetAssignmentValidator

    @content_json
    def GET(self, node_id):
        node = self.render(self.get_object_or_404(Node, node_id))
        default_nets = self.get_default(node)
        return self.render(node)['interfaces']

    # @content_json
    # def PUT(self, node_id):
    #     node = self.render(self.get_object_or_404(Node, node_id))
    #     node = self.get_default(node)
    #     self.update_attributes(node)


class NodeCollectionNICsDefaultHandler(NodeNICsDefaultHandler):

    validator = NetAssignmentValidator

    @content_json
    def GET(self):
        user_data = web.input(cluster_id=None)
        if user_data.cluster_id == '':
            nodes = self.get_object_or_404(Node, cluster_id=None)
        elif user_data.cluster_id:
            nodes = self.get_object_or_404(
                Node,
                cluster_id=user_data.cluster_id
            )
        else:
            nodes = self.get_object_or_404(Node)
        def_net_nodes = []
        for node in nodes:
            rendered_node = self.get_default(self.render(node))
            def_net_nodes.append(rendered_node)
        return map(self.render, nodes)

    # @content_json
    # def PUT(self):
    #     data = self.validator.validate_collection_structure(web.data())
    #     self.update_collection_attributes(data)


class NodeNICsVerifyHandler(JSONHandler, NICUtils):
    fields = (
        'id', (
            'interfaces',
            'id',
            'mac',
            'name',
            ('assigned_networks', 'id', 'name'),
            ('allowed_networks', 'id', 'name')
        )
    )

    validator = NetAssignmentValidator

    @content_json
    def POST(self):
        data = self.validator.validate_structure(web.data())
        for node in data:
            self.validator.verify_data_correctness(node)
        if TopoChecker.is_assignment_allowed(data):
            return map(self.render, nodes)
        topo = TopoChecker.resolve_topo_conflicts(data)
        ret = map(self.render, topo, fields=fields_with_conflicts)
        return map(self.render, topo, fields=fields_with_conflicts)
