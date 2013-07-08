# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import traceback
from datetime import datetime

import web

from nailgun.db import db
from nailgun import notifier
from nailgun.logger import logger
from nailgun.errors import errors
from nailgun.api.models import Node
from nailgun.api.models import Network
from nailgun.api.models import NetworkAssignment
from nailgun.api.models import NodeNICInterface
from nailgun.api.models import NetworkGroup
from nailgun.network.topology import TopoChecker
from nailgun.api.validators.node import NodeValidator
from nailgun.api.validators.node import NodeAttributesValidator
from nailgun.api.validators.node import NodeVolumesValidator
from nailgun.api.validators.network import NetAssignmentValidator
from nailgun.network.manager import NetworkManager
from nailgun.volumes.manager import VolumeManager
from nailgun.api.models import Node, NodeAttributes
from nailgun.api.handlers.base import JSONHandler, content_json


class NodeHandler(JSONHandler):
    fields = ('id', 'name', 'meta', 'role', 'progress',
              'status', 'mac', 'fqdn', 'ip', 'manufacturer', 'platform_name',
              'pending_addition', 'pending_deletion', 'os_platform',
              'error_type', 'online', 'cluster')
    model = Node
    validator = NodeValidator

    @classmethod
    def render(cls, instance, fields=None):
        json_data = None
        try:
            json_data = JSONHandler.render(instance, fields=cls.fields)
            network_manager = NetworkManager()
            json_data['network_data'] = network_manager.get_node_networks(
                instance.id)
        except:
            logger.error(traceback.format_exc())
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

        data = self.checked_data(self.validator.validate_update)

        network_manager = NetworkManager()

        for key, value in data.iteritems():
            # we don't allow to update id explicitly
            if key == "id":
                continue
            setattr(node, key, value)
            if key == 'cluster_id':
                if value:
                    network_manager.allow_network_assignment_to_all_interfaces(
                        node.id
                    )
                    network_manager.assign_networks_to_main_interface(node.id)
                else:
                    network_manager.clear_assigned_networks(node.id)
                    network_manager.clear_all_allowed_networks(node.id)
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
        db().commit()
        return self.render(node)

    def DELETE(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        db().delete(node)
        db().commit()
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
            nodes = db().query(Node).filter_by(
                cluster_id=None).all()
        elif user_data.cluster_id:
            nodes = db().query(Node).filter_by(
                cluster_id=user_data.cluster_id).all()
        else:
            nodes = db().query(Node).all()
        return map(NodeHandler.render, nodes)

    @content_json
    def POST(self):
        data = self.checked_data()

        node = Node()
        for key, value in data.iteritems():
            if key == "id":
                continue
            elif key == "meta":
                node.create_meta(value)
            else:
                setattr(node, key, value)
        node.name = "Untitled (%s)" % data['mac'][-5:]
        node.timestamp = datetime.now()
        db().add(node)
        db().commit()
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
                u"Failed to generate volumes "
                "info for node '{0}': '{1}'"
            ).format(
                node.name or data.get("mac") or data.get("id"),
                str(exc) or "see logs for details"
            )
            logger.warning(traceback.format_exc())
            notifier.notify("error", msg, node_id=node.id)
        db().add(node)
        db().commit()

        network_manager = NetworkManager()
        # Add interfaces for node from 'meta'.
        if node.meta and node.meta.get('interfaces'):
            network_manager.update_interfaces_info(node.id)

        if node.cluster_id:
            network_manager.allow_network_assignment_to_all_interfaces(node.id)
            network_manager.assign_networks_to_main_interface(node.id)

        try:
            ram = str(round(float(
                node.meta['memory']['total']) / 1073741824, 1))
        except (KeyError, TypeError, ValueError):
            ram = "unknown"

        try:
            hd_size = str(round(float(
                sum([d["size"] for d in node.meta["disks"]]) / 1073741824), 1))
        except KeyError:
            hd_size = "unknown"

        cores = str(node.meta.get('cpu', {}).get('total', "unknown"))
        notifier.notify("discover",
                        "New node with %s CPU core(s), %s GB HDD "
                        "and %s GB memory is discovered" %
                        (cores, hd_size, ram), node_id=node.id)
        raise web.webapi.created(json.dumps(
            NodeHandler.render(node),
            indent=4
        ))

    @content_json
    def PUT(self):
        data = self.checked_data(
            self.validator.validate_collection_update
        )

        network_manager = NetworkManager()
        q = db().query(Node)
        nodes_updated = []
        for nd in data:
            is_agent = nd.pop("is_agent") if "is_agent" in nd else False
            node = None
            if "mac" in nd:
                node = q.filter_by(mac=nd["mac"]).first() \
                    or self.validator.validate_existent_node_mac_update(nd)
            else:
                node = q.get(nd["id"])
            if is_agent:
                node.timestamp = datetime.now()
                if not node.online:
                    node.online = True
                    msg = u"Node '{0}' is back online".format(
                        node.human_readable_name)
                    logger.info(msg)
                    notifier.notify("discover", msg, node_id=node.id)
                db().commit()
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
                if key == "meta":
                    node.update_meta(value)
                else:
                    setattr(node, key, value)
            db().commit()
            if not node.attributes:
                node.attributes = NodeAttributes()
                db().commit()
            if not node.attributes.volumes:
                node.attributes.volumes = \
                    node.volume_manager.gen_volumes_info()
                db().commit()
            if not node.status in ('provisioning', 'deploying'):
                variants = (
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

                db().commit()
            if is_agent:
                # Update node's NICs.
                if node.meta and 'interfaces' in node.meta:
                    # we won't update interfaces if data is invalid
                    network_manager.update_interfaces_info(node.id)

            nodes_updated.append(node)
            db().commit()
            if 'cluster_id' in nd and nd['cluster_id'] != old_cluster_id:
                if old_cluster_id:
                    network_manager.clear_assigned_networks(node.id)
                    network_manager.clear_all_allowed_networks(node.id)
                if nd['cluster_id']:
                    network_manager.allow_network_assignment_to_all_interfaces(
                        node.id
                    )
                    network_manager.assign_networks_to_main_interface(node.id)
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
        db().commit()
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
        db().commit()
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
        if attr_name == "volumes":
            data = NodeVolumesValidator.validate(data)
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
                    updated = False
                    for i, e in enumerate(attr):
                        if (a.get("type") == e.get("type") and
                                a.get("id") == e.get("id")):
                            attr[i] = a
                            updated = True
                            break
                    if not updated:
                        attr.append(a)

                attr = filter(
                    lambda a: a["type"] == attr_params.type,
                    getattr(node_attrs, attr_name)
                )
        else:
            setattr(node_attrs, attr_name, data)
            attr = getattr(node_attrs, attr_name)
        return attr


class NodeNICsHandler(JSONHandler):
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


class NodeCollectionNICsHandler(JSONHandler):

    model = NetworkGroup
    validator = NetAssignmentValidator
    fields = NodeNICsHandler.fields

    @content_json
    def PUT(self):
        data = self.validator.validate_collection_structure(web.data())
        network_manager = NetworkManager()
        updated_nodes_ids = []
        for node_data in data:
            self.validator.verify_data_correctness(node_data)
            node_id = network_manager._update_attrs(node_data)
            updated_nodes_ids.append(node_id)
        updated_nodes = db().query(Node).filter(
            Node.id.in_(updated_nodes_ids)
        ).all()
        return map(self.render, updated_nodes)


class NodeNICsDefaultHandler(JSONHandler):

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        default_nets = self.get_default(node)
        return default_nets

    def get_default(self, node):
        nics = []
        network_manager = NetworkManager()
        for nic in node.interfaces:
            nic_dict = {
                "id": nic.id,
                "name": nic.name,
                "mac": nic.mac,
                "max_speed": nic.max_speed,
                "current_speed": nic.current_speed
            }

            assigned_ng_ids = network_manager.get_default_nic_networkgroups(
                node.id,
                nic.id
            )
            for ng_id in assigned_ng_ids:
                ng = db().query(NetworkGroup).get(ng_id)
                nic_dict.setdefault("assigned_networks", []).append(
                    {"id": ng_id, "name": ng.name}
                )

            allowed_ng_ids = network_manager.get_allowed_nic_networkgroups(
                node.id,
                nic.id
            )
            for ng_id in allowed_ng_ids:
                ng = db().query(NetworkGroup).get(ng_id)
                nic_dict.setdefault("allowed_networks", []).append(
                    {"id": ng_id, "name": ng.name}
                )

            nics.append(nic_dict)
        return nics


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


class NodeNICsVerifyHandler(JSONHandler):
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
