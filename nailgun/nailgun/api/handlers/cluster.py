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
from nailgun.api.validators import NetworkGroupValidator
from nailgun.api.validators import AttributesValidator
from nailgun.network.manager import NetworkManager
from nailgun.network.errors import OutOfVLANs
from nailgun.network.errors import OutOfIPs
from nailgun.network.errors import NoSuitableCIDR
from nailgun.api.handlers.base import JSONHandler, content_json
from nailgun.api.handlers.node import NodeHandler
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.task.helpers import update_task_status
from nailgun.task.manager import DeploymentTaskManager
from nailgun.task.manager import ClusterDeletionManager


class ClusterHandler(JSONHandler):
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
            json_data["changes"] = [
                i.name for i in instance.changes if not i.node_id
            ]
            json_data["changes"].extend([
                [i.name, i.node_id] for i in instance.changes if i.node_id
            ])
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
                map(cluster.nodes.remove, cluster.nodes)
                nodes = self.db.query(Node).filter(
                    Node.id.in_(value)
                )
                map(cluster.nodes.append, nodes)
            else:
                setattr(cluster, key, value)
        self.db.add(cluster)
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


class ClusterCollectionHandler(JSONHandler):

    validator = ClusterValidator

    @content_json
    def GET(self):
        return map(
            ClusterHandler.render,
            self.db.query(Cluster).all()
        )

    @content_json
    def POST(self):
        data = self.validator.validate(web.data())

        cluster = Cluster()
        cluster.release = self.db.query(Release).get(data["release"])
        # TODO: use fields
        for field in ('name', 'type', 'mode', 'net_manager'):
            if data.get(field):
                setattr(cluster, field, data.get(field))
        self.db.add(cluster)
        self.db.commit()

        if 'nodes' in data and data['nodes']:
            nodes = self.db.query(Node).filter(
                Node.id.in_(data['nodes'])
            ).all()
            map(cluster.nodes.append, nodes)
        self.db.commit()

        attributes = Attributes(
            editable=cluster.release.attributes_metadata.get("editable"),
            generated=cluster.release.attributes_metadata.get("generated"),
            cluster=cluster
        )
        attributes.generate_fields()

        netmanager = NetworkManager()
        netmanager.create_network_groups(cluster.id)

        cluster.add_pending_changes("attributes")
        cluster.add_pending_changes("networks")

        raise web.webapi.created(json.dumps(
            ClusterHandler.render(cluster),
            indent=4
        ))


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
                "with id '{0}' in DB.".format(cluster_id)
            )
        )

        task_manager = DeploymentTaskManager(cluster_id=cluster.id)
        try:
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
