# -*- coding: utf-8 -*-

import json
import traceback
import web
import netaddr

from nailgun.settings import settings
from nailgun.logger import logger
from nailgun.errors import errors
from nailgun.api.models import Cluster
from nailgun.api.models import Node
from nailgun.api.models import Network, NetworkGroup, Vlan
from nailgun.api.models import Release
from nailgun.api.models import Attributes
from nailgun.api.models import Task
from nailgun.api.validators import ClusterValidator
from nailgun.api.validators import AttributesValidator
from nailgun.network.manager import NetworkManager
from nailgun.api.handlers.base import JSONHandler, content_json
from nailgun.api.handlers.node import NodeHandler
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.task.helpers import TaskHelper
from nailgun.task.manager import DeploymentTaskManager
from nailgun.task.manager import ClusterDeletionManager
from nailgun.task.manager import CheckBeforeDeploymentTaskManager

from nailgun.network.topology import NICUtils


class ClusterHandler(JSONHandler, NICUtils):
    fields = (
        "id",
        "name",
        "type",
        "mode",
        "status",
        ("release", "*")
    )
    model = Cluster
    validator = ClusterValidator

    @classmethod
    def render(cls, instance, fields=None):
        json_data = JSONHandler.render(instance, fields=cls.fields)
        if instance.changes:
            for i in instance.changes:
                if not i.node_id:
                    json_data.setdefault("changes", []).append(i.name)
                else:
                    json_data.setdefault("changes", []).append(
                        [i.name, i.node_id, i.node.name]
                    )
        else:
            json_data["changes"] = []
        return json_data

    @content_json
    def GET(self, cluster_id):
        cluster = self.get_object_or_404(Cluster, cluster_id)
        return self.render(cluster)

    @content_json
    def PUT(self, cluster_id):
        cluster = self.get_object_or_404(Cluster, cluster_id)
        data = self.validator.validate(web.data())
        for key, value in data.iteritems():
            if key == "nodes":
                # Todo: sepatate nodes for deletion and addition by set().
                new_nodes = self.db.query(Node).filter(
                    Node.id.in_(value)
                )
                nodes_to_remove = [n for n in cluster.nodes
                                   if n not in new_nodes]
                nodes_to_add = [n for n in new_nodes
                                if n not in cluster.nodes]
                for node in nodes_to_add:
                    if not node.online:
                        raise web.badrequest(
                            "Can not add offline node to cluster")
                map(cluster.nodes.remove, nodes_to_remove)
                map(cluster.nodes.append, nodes_to_add)
                for node in nodes_to_remove:
                    self.clear_assigned_networks(node)
                    self.clear_all_allowed_networks(node)
                for node in nodes_to_add:
                    self.allow_network_assignment_to_all_interfaces(node)
                    self.assign_networks_to_main_interface(node)
            else:
                setattr(cluster, key, value)
        self.db.commit()
        return self.render(cluster)

    @content_json
    def DELETE(self, cluster_id):
        cluster = self.get_object_or_404(Cluster, cluster_id)
        task_manager = ClusterDeletionManager(cluster_id=cluster.id)
        try:
            logger.debug('Trying to execute cluster deletion task')
            task = task_manager.execute()
        except Exception as e:
            logger.warn('Error while execution '
                        'cluster deletion task: %s' % str(e))
            logger.warn(traceback.format_exc())
            raise web.badrequest(str(e))
        raise web.webapi.HTTPError(
            status="202 Accepted",
            data="{}"
        )


class ClusterCollectionHandler(JSONHandler, NICUtils):

    validator = ClusterValidator

    @content_json
    def GET(self):
        return map(
            ClusterHandler.render,
            self.db.query(Cluster).all()
        )

    @content_json
    def POST(self):
        # It's used for cluster creating only.
        data = self.validator.validate(web.data())

        cluster = Cluster()
        cluster.release = self.db.query(Release).get(data["release"])
        # TODO: use fields
        for field in ('name', 'type', 'mode', 'net_manager'):
            if data.get(field):
                setattr(cluster, field, data.get(field))
        self.db.add(cluster)
        self.db.commit()
        attributes = Attributes(
            editable=cluster.release.attributes_metadata.get("editable"),
            generated=cluster.release.attributes_metadata.get("generated"),
            cluster=cluster
        )
        attributes.generate_fields()

        netmanager = NetworkManager(self.db)
        try:
            netmanager.create_network_groups(cluster.id)

            cluster.add_pending_changes("attributes")
            cluster.add_pending_changes("networks")

            if 'nodes' in data and data['nodes']:
                nodes = self.db.query(Node).filter(
                    Node.id.in_(data['nodes'])
                ).all()
                map(cluster.nodes.append, nodes)
                for node in nodes:
                    self.allow_network_assignment_to_all_interfaces(node)
                    self.assign_networks_to_main_interface(node)
                self.db.commit()

            raise web.webapi.created(json.dumps(
                ClusterHandler.render(cluster),
                indent=4
            ))
        except errors.OutOfVLANs as e:
            # Cluster was created in this request,
            # so we no need to use ClusterDeletionManager.
            # All relations wiil be cascade deleted automaticly.
            # TODO: investigate transactions
            self.db.delete(cluster)

            raise web.badrequest(e.message)


class ClusterChangesHandler(JSONHandler):
    fields = (
        "id",
        "name",
    )

    @content_json
    def PUT(self, cluster_id):
        cluster = self.get_object_or_404(
            Cluster,
            cluster_id,
            log_404=(
                "warning",
                "Error: there is no cluster "
                "with id '{0}' in DB.".format(cluster_id)))

        check_task_manager = CheckBeforeDeploymentTaskManager(
            cluster_id=cluster.id)
        check_task = check_task_manager.execute()
        if check_task.status == 'error':
            return TaskHandler.render(check_task)

        try:
            task_manager = DeploymentTaskManager(cluster_id=cluster.id)
            task = task_manager.execute()
        except Exception as exc:
            logger.warn(u'ClusterChangesHandler: error while execution'
                        ' deploy task: {0}'.format(exc.message))
            raise web.badrequest(exc.message)
        return TaskHandler.render(task)


class ClusterAttributesHandler(JSONHandler):
    fields = (
        "editable",
    )

    validator = AttributesValidator

    @content_json
    def GET(self, cluster_id):
        cluster = self.get_object_or_404(Cluster, cluster_id)
        if not cluster.attributes:
            raise web.internalerror("No attributes found!")

        return {
            "editable": cluster.attributes.editable
        }

    @content_json
    def PUT(self, cluster_id):
        cluster = self.get_object_or_404(Cluster, cluster_id)
        if not cluster.attributes:
            raise web.internalerror("No attributes found!")

        data = self.validator.validate(web.data())

        for key, value in data.iteritems():
            setattr(cluster.attributes, key, value)
        cluster.add_pending_changes("attributes")

        self.db.commit()
        return {"editable": cluster.attributes.editable}


class ClusterAttributesDefaultsHandler(JSONHandler):
    fields = (
        "editable",
    )

    @content_json
    def GET(self, cluster_id):
        cluster = self.get_object_or_404(Cluster, cluster_id)
        attrs = cluster.release.attributes_metadata.get("editable")
        if not attrs:
            raise web.internalerror("No attributes found!")
        return {"editable": attrs}

    @content_json
    def PUT(self, cluster_id):
        cluster = self.get_object_or_404(
            Cluster,
            cluster_id,
            log_404=(
                "warning",
                "Error: there is no cluster "
                "with id '{0}' in DB.".format(cluster_id)
            )
        )

        if not cluster.attributes:
            logger.error('ClusterAttributesDefaultsHandler: no attributes'
                         ' found for cluster_id %s' % cluster_id)
            raise web.internalerror("No attributes found!")

        cluster.attributes.editable = cluster.release.attributes_metadata.get(
            "editable"
        )
        self.db.commit()
        cluster.add_pending_changes("attributes")

        logger.debug('ClusterAttributesDefaultsHandler:'
                     ' editable attributes for cluster_id %s were reset'
                     ' to default' % cluster_id)
        return {"editable": cluster.attributes.editable}
