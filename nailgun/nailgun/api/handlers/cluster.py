# -*- coding: utf-8 -*-

import json
import uuid
import itertools

import web
import netaddr

import nailgun.rpc as rpc
from nailgun.settings import settings
from nailgun.logger import logger
from nailgun.api.models import Cluster
from nailgun.api.models import Node
from nailgun.api.models import Network
from nailgun.api.models import Release
from nailgun.api.models import Attributes
from nailgun.api.models import NetworkElement
from nailgun.api.models import Vlan
from nailgun.api.models import Task

from nailgun.api.handlers.base import JSONHandler
from nailgun.api.handlers.node import NodeHandler
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.task.manager import DeploymentTaskManager
from nailgun.task.manager import ClusterDeletionManager
from nailgun.task.manager import VerifyNetworksTaskManager
from nailgun.task.errors import FailedProvisioning
from nailgun.task.errors import DeploymentAlreadyStarted
from nailgun.task.errors import WrongNodeStatus


class ClusterHandler(JSONHandler):
    fields = (
        "id",
        "name",
        "type",
        "mode",
        "status",
        ("nodes", "*"),
        ("release", "*")
    )
    model = Cluster

    @classmethod
    def render(cls, instance, fields=None):
        json_data = JSONHandler.render(instance, fields=cls.fields)
        json_data["tasks"] = map(
            TaskHandler.render,
            instance.tasks
        )
        return json_data

    def GET(self, cluster_id):
        web.header('Content-Type', 'application/json')
        q = web.ctx.orm.query(Cluster)
        cluster = q.get(cluster_id)
        if not cluster:
            return web.notfound()
        return json.dumps(
            self.render(cluster),
            indent=4
        )

    def PUT(self, cluster_id):
        web.header('Content-Type', 'application/json')
        cluster = web.ctx.orm.query(Cluster).get(cluster_id)
        if not cluster:
            return web.notfound()
        # additional validation needed?
        data = Cluster.validate_json(web.data())
        # /additional validation needed?
        for key, value in data.iteritems():
            if key == "nodes":
                map(cluster.nodes.remove, cluster.nodes)
                nodes = web.ctx.orm.query(Node).filter(
                    Node.id.in_(value)
                )
                map(cluster.nodes.append, nodes)
            else:
                setattr(cluster, key, value)
        web.ctx.orm.add(cluster)
        web.ctx.orm.commit()
        return json.dumps(
            self.render(cluster),
            indent=4
        )

    def DELETE(self, cluster_id):
        web.header('Content-Type', 'application/json')

        cluster = web.ctx.orm.query(Cluster).get(cluster_id)
        if not cluster:
            return web.notfound()

        task_manager = ClusterDeletionManager(cluster_id=cluster.id)
        try:
            logger.debug('Trying to execute cluster deletion task')
            task = task_manager.execute()
            logger.debug('Cluster deletion task: %s' % task.uuid)
        except Exception as e:
            logger.warn('Error while execution '
                        'cluster deletion task: %s' % str(e))
            raise web.badrequest(str(e))

        raise web.webapi.HTTPError(
            status="202 Accepted",
            data=""
        )


class ClusterCollectionHandler(JSONHandler):
    def GET(self):
        web.header('Content-Type', 'application/json')
        return json.dumps(map(
            ClusterHandler.render,
            web.ctx.orm.query(Cluster).all()
        ), indent=4)

    def POST(self):
        web.header('Content-Type', 'application/json')
        data = Cluster.validate(web.data())

        cluster = Cluster()
        cluster.release = web.ctx.orm.query(Release).get(data["release"])

        # TODO: discover how to add multiple objects
        if 'nodes' in data and data['nodes']:
            nodes = web.ctx.orm.query(Node).filter(
                Node.id.in_(data['nodes'])
            )
            map(cluster.nodes.append, nodes)

        # TODO: use fields
        for field in ('name', 'type', 'mode'):
            setattr(cluster, field, data.get(field))

        web.ctx.orm.add(cluster)
        web.ctx.orm.commit()
        attributes = Attributes(
            editable=cluster.release.attributes_metadata.get("editable"),
            generated=cluster.release.attributes_metadata.get("generated"),
            cluster=cluster
        )
        web.ctx.orm.add(attributes)
        web.ctx.orm.commit()
        attributes.generate_fields()
        web.ctx.orm.add(attributes)
        web.ctx.orm.commit()

        used_nets = [n.cidr for n in web.ctx.orm.query(Network).all()]
        used_vlans = [v.id for v in web.ctx.orm.query(Vlan).all()]

        for network in cluster.release.networks_metadata:
            new_vlan = sorted(list(set(range(int(settings.VLANS_RANGE_START),
                                             int(settings.VLANS_RANGE_END))) -
                                   set(used_vlans)))[0]
            vlan_db = Vlan(id=new_vlan)
            web.ctx.orm.add(vlan_db)
            web.ctx.orm.commit()

            pool = settings.NETWORK_POOLS[network['access']]
            nets_free_set = netaddr.IPSet(pool) -\
                netaddr.IPSet(settings.NET_EXCLUDE) -\
                netaddr.IPSet(used_nets)

            free_cidrs = sorted(list(nets_free_set._cidrs))
            new_net = list(free_cidrs[0].subnet(24, count=1))[0]

            nw_db = Network(
                release=cluster.release.id,
                name=network['name'],
                access=network['access'],
                cidr=str(new_net),
                gateway=str(new_net[1]),
                cluster_id=cluster.id,
                vlan_id=vlan_db.id
            )
            web.ctx.orm.add(nw_db)
            web.ctx.orm.commit()

            used_vlans.append(new_vlan)
            used_nets.append(str(new_net))

        raise web.webapi.created(json.dumps(
            ClusterHandler.render(cluster),
            indent=4
        ))


class ClusterChangesHandler(JSONHandler):
    fields = (
        "id",
        "name",
    )

    def PUT(self, cluster_id):
        web.header('Content-Type', 'application/json')
        cluster = web.ctx.orm.query(Cluster).get(cluster_id)
        logger.debug('ClusterChangesHandler: PUT request with cluster_id %s' %
                     cluster_id)
        if not cluster:
            logger.warn('ClusterChangesHandler: there is'
                        ' no cluster with id %s in DB.' % cluster_id)
            return web.notfound()

        task_manager = DeploymentTaskManager(cluster_id=cluster.id)
        try:
            logger.debug('ClusterChangesHandler: trying to execute task...')
            task = task_manager.execute()
            logger.debug('ClusterChangesHandler: task to deploy is %s' %
                         task.uuid)
        except (DeploymentAlreadyStarted,
                FailedProvisioning,
                WrongNodeStatus) as exc:
            logger.warn('ClusterChangesHandler: error while execution'
                        ' deploy task: %s' % exc.message)
            raise web.badrequest(exc.message)

        return json.dumps(
            TaskHandler.render(task),
            indent=4
        )


class ClusterNetworksHandler(JSONHandler):
    fields = (
        "id",
        "name",
    )

    def PUT(self, cluster_id):
        web.header('Content-Type', 'application/json')
        cluster = web.ctx.orm.query(Cluster).get(cluster_id)
        if not cluster:
            return web.notfound()

        task_manager = VerifyNetworksTaskManager(cluster_id=cluster.id)
        task = task_manager.execute()

        return json.dumps(
            TaskHandler.render(task),
            indent=4
        )


class ClusterAttributesHandler(JSONHandler):
    fields = (
        "editable",
    )

    def GET(self, cluster_id):
        web.header('Content-Type', 'application/json')
        cluster = web.ctx.orm.query(Cluster).get(cluster_id)
        if not cluster:
            return web.notfound()

        attrs = cluster.attributes
        if not attrs:
            raise web.internalerror("No attributes found!")

        return json.dumps(
            {
                "editable": attrs.editable
            },
            indent=4
        )

    def PUT(self, cluster_id):
        web.header('Content-Type', 'application/json')
        cluster = web.ctx.orm.query(Cluster).get(cluster_id)
        if not cluster:
            return web.notfound()

        attrs = cluster.attributes
        if not attrs:
            raise web.internalerror("No attributes found!")

        data = Attributes.validate(web.data())

        for key, value in data.iteritems():
            setattr(attrs, key, value)

        web.ctx.orm.add(attrs)
        web.ctx.orm.commit()

        return json.dumps(
            {
                "editable": attrs.editable
            },
            indent=4
        )


class ClusterAttributesDefaultsHandler(JSONHandler):
    fields = (
        "editable",
    )

    def PUT(self, cluster_id):
        logger.debug('ClusterAttributesDefaultsHandler:'
                     ' PUT request with cluster_id %s' % cluster_id)
        web.header('Content-Type', 'application/json')
        cluster = web.ctx.orm.query(Cluster).get(cluster_id)
        if not cluster:
            logger.warn('ClusterAttributesDefaultsHandler: there is'
                        ' no cluster with id %s in DB.' % cluster_id)
            return web.notfound()

        attrs = cluster.attributes
        if not attrs:
            logger.error('ClusterAttributesDefaultsHandler: no attributes'
                         ' found for cluster_id %s' % cluster_id)
            raise web.internalerror("No attributes found!")

        attrs.editable = cluster.release.attributes_metadata.get("editable")
        web.ctx.orm.add(attrs)
        web.ctx.orm.commit()

        logger.debug('ClusterAttributesDefaultsHandler:'
                     ' editable attributes for cluster_id %s were reset'
                     ' to default' % cluster_id)
        return json.dumps(
            {
                "editable": attrs.editable
            },
            indent=4
        )
