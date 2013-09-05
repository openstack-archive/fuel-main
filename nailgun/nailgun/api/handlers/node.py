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

"""
Handlers dealing with nodes
"""

from datetime import datetime
import json
import traceback

import web

from nailgun.api.handlers.base import content_json
from nailgun.api.handlers.base import JSONHandler
from nailgun.api.models import Cluster
from nailgun.api.models import NetworkGroup
from nailgun.api.models import Node
from nailgun.api.models import NodeAttributes
from nailgun.api.models import NodeNICInterface
from nailgun.api.validators.network import NetAssignmentValidator
from nailgun.api.validators.node import NodeValidator
from nailgun.db import db
from nailgun.logger import logger
from nailgun.network.manager import NetworkManager
from nailgun.network.topology import TopoChecker
from nailgun import notifier


class NodeHandler(JSONHandler):
    fields = ('id', 'name', 'meta', 'progress', 'roles', 'pending_roles',
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
        except Exception:
            logger.error(traceback.format_exc())
        return json_data

    @content_json
    def GET(self, node_id):
        """:returns: JSONized Node object.
        :http: * 200 (OK)
               * 404 (node not found in db)
        """
        node = self.get_object_or_404(Node, node_id)
        return self.render(node)

    @content_json
    def PUT(self, node_id):
        """:returns: JSONized Node object.
        :http: * 200 (OK)
               * 400 (invalid node data specified)
               * 404 (node not found in db)
        """
        node = self.get_object_or_404(Node, node_id)
        if not node.attributes:
            node.attributes = NodeAttributes(node_id=node.id)

        data = self.checked_data(self.validator.validate_update)

        network_manager = NetworkManager()

        if "cluster_id" in data:
            if data["cluster_id"] is None and node.cluster:
                node.cluster.clear_pending_changes(node_id=node.id)
                node.roles = node.pending_roles = []
            old_cluster_id = node.cluster_id
            node.cluster_id = data["cluster_id"]
            if node.cluster_id != old_cluster_id:
                if old_cluster_id:
                    network_manager.clear_assigned_networks(node.id)
                    network_manager.clear_all_allowed_networks(node.id)
                if node.cluster_id:
                    network_manager.allow_network_assignment_to_all_interfaces(
                        node.id
                    )
                    network_manager.assign_networks_to_main_interface(node.id)
        for key, value in data.iteritems():
            # we don't allow to update id explicitly
            # and updated cluster_id before all other fields
            if key in ("id", "cluster_id"):
                continue
            setattr(node, key, value)
        if not node.status in ('provisioning', 'deploying') \
                and "roles" in data or "cluster_id" in data:
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
        """:returns: Empty string
        :http: * 204 (node successfully deleted)
               * 404 (cluster not found in db)
        """
        node = self.get_object_or_404(Node, node_id)
        db().delete(node)
        db().commit()
        raise web.webapi.HTTPError(
            status="204 No Content",
            data=""
        )


class NodeCollectionHandler(JSONHandler):
    """Node collection handler
    """

    validator = NodeValidator

    @content_json
    def GET(self):
        """May receive cluster_id parameter to filter list
        of nodes

        :returns: Collection of JSONized Node objects.
        :http: * 200 (OK)
        """
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
        """:returns: JSONized Node object.
        :http: * 201 (cluster successfully created)
               * 400 (invalid node data specified)
               * 403 (node has incorrect status)
               * 409 (node with such parameters already exists)
        """
        data = self.checked_data()

        if data.get("status", "") != "discover":
            error = web.forbidden()
            error.data = "Only bootstrap nodes are allowed to be registered."
            msg = u"Node with mac '{0}' was not created, " \
                  u"because request status is '{1}'."\
                .format(data[u'mac'], data[u'status'])
            logger.info(msg)
            raise error

        node = Node()
        if "cluster_id" in data:
            # FIXME(vk): this part is needed only for tests. Normally,
            # nodes are created only by agent and POST requests don't contain
            # cluster_id, but our integration and unit tests widely use it.
            # We need to assign cluster first
            cluster_id = data.pop("cluster_id")
            if cluster_id:
                node.cluster = db.query(Cluster).get(cluster_id)
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
            # we use multiplier of 1024 because there are no problems here
            # with unfair size calculation
            ram = str(round(float(
                node.meta['memory']['total']) / 1073741824, 1)) + " GB RAM"
        except Exception as exc:
            logger.warning(traceback.format_exc())
            ram = "unknown RAM"

        try:
            # we use multiplier of 1000 because disk vendors specify HDD size
            # in terms of decimal capacity. Sources:
            # http://knowledge.seagate.com/articles/en_US/FAQ/172191en
            # http://physics.nist.gov/cuu/Units/binary.html
            hd_size = round(float(
                sum([d["size"] for d in node.meta["disks"]]) / 1000000000), 1)
            # if HDD > 100 GB we show it's size in TB
            if hd_size > 100:
                hd_size = str(hd_size / 1000) + " TB HDD"
            else:
                hd_size = str(hd_size) + " GB HDD"
        except Exception as exc:
            logger.warning(traceback.format_exc())
            hd_size = "unknown HDD"

        cores = str(node.meta.get('cpu', {}).get('total', "unknown"))
        notifier.notify(
            "discover",
            "New node is discovered: %s CPUs / %s / %s " %
            (cores, ram, hd_size),
            node_id=node.id
        )
        raise web.webapi.created(json.dumps(
            NodeHandler.render(node),
            indent=4
        ))

    @content_json
    def PUT(self):
        """:returns: Collection of JSONized Node objects.
        :http: * 200 (nodes are successfully updated)
               * 400 (invalid nodes data specified)
        """
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
            old_cluster_id = node.cluster_id
            if "cluster_id" in nd:
                if nd["cluster_id"] is None and node.cluster:
                    node.cluster.clear_pending_changes(node_id=node.id)
                    node.roles = node.pending_roles = []
                node.cluster_id = nd["cluster_id"]
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
                    "roles" in nd,
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


class NodeNICsHandler(JSONHandler):
    """Node network interfaces handler
    """

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
        """:returns: Collection of JSONized Node interfaces.
        :http: * 200 (OK)
               * 404 (node not found in db)
        """
        node = self.get_object_or_404(Node, node_id)
        return self.render(node)['interfaces']


class NodeCollectionNICsHandler(JSONHandler):
    """Node collection network interfaces handler
    """

    model = NetworkGroup
    validator = NetAssignmentValidator
    fields = NodeNICsHandler.fields

    @content_json
    def PUT(self):
        """:returns: Collection of JSONized Node objects.
        :http: * 200 (nodes are successfully updated)
               * 400 (invalid nodes data specified)
        """
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
    """Node default network interfaces handler
    """

    @content_json
    def GET(self, node_id):
        """:returns: Collection of default JSONized interfaces for node.
        :http: * 200 (OK)
               * 404 (node not found in db)
        """
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
    """Node collection default network interfaces handler
    """

    validator = NetAssignmentValidator

    @content_json
    def GET(self):
        """May receive cluster_id parameter to filter list
        of nodes

        :returns: Collection of JSONized Nodes interfaces.
        :http: * 200 (OK)
               * 404 (node not found in db)
        """
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
    """Node NICs verify handler
    Class is proof of concept. Not ready for use.
    """

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
        """:returns: Collection of JSONized Nodes interfaces.
        :http: * 200 (OK)
        """
        data = self.validator.validate_structure(web.data())
        for node in data:
            self.validator.verify_data_correctness(node)
        if TopoChecker.is_assignment_allowed(data):
            return map(self.render, data)
        topo, fields_with_conflicts = TopoChecker.resolve_topo_conflicts(data)
        return map(self.render, topo, fields=fields_with_conflicts)


class NodesAllocationStatsHandler(object):
    """Node allocation stats handler
    """

    @content_json
    def GET(self):
        """:returns: Total and unallocated nodes count.
        :http: * 200 (OK)
        """
        unallocated_nodes = db().query(Node).filter_by(cluster_id=None).count()
        total_nodes = \
            db().query(Node).count()
        return {'total': total_nodes,
                'unallocated': unallocated_nodes}
