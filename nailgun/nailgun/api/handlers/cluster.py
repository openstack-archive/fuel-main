# -*- coding: utf-8 -*-

import json
import uuid
import itertools
import traceback

import web
import netaddr

import nailgun.rpc as rpc
from nailgun.db import orm
from nailgun.settings import settings
from nailgun.logger import logger
from nailgun.api.models import Cluster
from nailgun.api.models import Node
from nailgun.api.models import Network, NetworkElement, NetworkGroup, Vlan
from nailgun.api.models import Release
from nailgun.api.models import Attributes
from nailgun.api.models import Task

from nailgun.api.handlers.base import JSONHandler
from nailgun.api.handlers.node import NodeHandler
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.task.helpers import update_task_status
from nailgun.task.manager import DeploymentTaskManager
from nailgun.task.manager import ClusterDeletionManager
from nailgun.task.manager import VerifyNetworksTaskManager
from nailgun.task.manager import CheckNetworksTaskManager
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
        "net_manager",
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
        if instance.changes:
            json_data["changes"] = [
                i.name for i in instance.changes
            ]
        else:
            json_data["changes"] = []
        return json_data

    def GET(self, cluster_id):
        web.header('Content-Type', 'application/json')
        q = orm().query(Cluster)
        cluster = q.get(cluster_id)
        if not cluster:
            return web.notfound()
        return json.dumps(
            self.render(cluster),
            indent=4
        )

    def PUT(self, cluster_id):
        web.header('Content-Type', 'application/json')
        cluster = orm().query(Cluster).get(cluster_id)
        if not cluster:
            return web.notfound()
        # additional validation needed?
        data = Cluster.validate_json(web.data())
        # /additional validation needed?
        for key, value in data.iteritems():
            if key == "nodes":
                map(cluster.nodes.remove, cluster.nodes)
                nodes = orm().query(Node).filter(
                    Node.id.in_(value)
                )
                map(cluster.nodes.append, nodes)
            else:
                setattr(cluster, key, value)
        orm().add(cluster)
        orm().commit()
        return json.dumps(
            self.render(cluster),
            indent=4
        )

    def DELETE(self, cluster_id):
        web.header('Content-Type', 'application/json')

        cluster = orm().query(Cluster).get(cluster_id)
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
            orm().query(Cluster).all()
        ), indent=4)

    def POST(self):
        web.header('Content-Type', 'application/json')
        data = Cluster.validate(web.data())

        cluster = Cluster()
        cluster.release = orm().query(Release).get(data["release"])

        # TODO: use fields
        for field in ('name', 'type', 'mode', 'net_manager'):
            if data.get(field):
                setattr(cluster, field, data.get(field))

        orm().add(cluster)
        orm().commit()

        # TODO: discover how to add multiple objects
        if 'nodes' in data and data['nodes']:
            nodes = orm().query(Node).filter(
                Node.id.in_(data['nodes'])
            ).all()
            map(cluster.nodes.append, nodes)
        orm().add(cluster)
        orm().commit()

        attributes = Attributes(
            editable=cluster.release.attributes_metadata.get("editable"),
            generated=cluster.release.attributes_metadata.get("generated"),
            cluster=cluster
        )
        orm().add(attributes)
        orm().commit()
        attributes.generate_fields()
        orm().add(attributes)
        orm().commit()

        used_nets = [n.cidr for n in orm().query(Network).all()]
        used_vlans = [v.id for v in orm().query(Vlan).all()]

        for network in cluster.release.networks_metadata:
            free_vlans = sorted(list(set(range(int(
                settings.VLANS_RANGE_START),
                int(settings.VLANS_RANGE_END))) -
                set(used_vlans)))
            if not free_vlans:
                orm().delete(cluster)
                orm().commit()
                raise web.conflict(
                    "There is not enough available VLAN IDs "
                    "to create the cluster"
                )
            vlan_start = free_vlans[0]
            logger.debug("Found free vlan: %s", vlan_start)

            pool = settings.NETWORK_POOLS[network['access']]
            nets_free_set = netaddr.IPSet(pool) -\
                netaddr.IPSet(settings.NET_EXCLUDE) -\
                netaddr.IPSet(used_nets)
            if not nets_free_set:
                orm().delete(cluster)
                orm().commit()
                raise web.conflict("No free IP addresses in pool")

            free_cidrs = sorted(list(nets_free_set._cidrs))
            new_net = None
            for fcidr in free_cidrs:
                for n in fcidr.subnet(24, count=1):
                    new_net = n
                    break
                if new_net:
                    break
            if not new_net:
                orm().delete(cluster)
                orm().commit()
                raise web.conflict("Cannot find suitable CIDR")

            nw_db = NetworkGroup(
                release=cluster.release.id,
                name=network['name'],
                access=network['access'],
                cidr=str(new_net),
                gateway_ip_index=1,
                cluster_id=cluster.id,
                vlan_start=vlan_start,
                amount=1
            )
            orm().add(nw_db)
            orm().commit()
            nw_db.create_networks()

            used_vlans.append(vlan_start)
            used_nets.append(str(new_net))

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

    def PUT(self, cluster_id):
        web.header('Content-Type', 'application/json')
        cluster = orm().query(Cluster).get(cluster_id)
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


class ClusterVerifyNetworksHandler(JSONHandler):
    fields = (
        "id",
        "name",
    )

    def PUT(self, cluster_id):
        web.header('Content-Type', 'application/json')
        cluster = orm().query(Cluster).get(cluster_id)
        if not cluster:
            return web.notfound()
        nets = NetworkGroup.validate_collection_update(web.data())
        if not nets:
            raise web.badrequest()
        vlan_ids = NetworkGroup.generate_vlan_ids_list(nets)

        task_manager = VerifyNetworksTaskManager(cluster_id=cluster.id)
        task = task_manager.execute(nets, vlan_ids)

        return json.dumps(
            TaskHandler.render(task),
            indent=4
        )


class ClusterSaveNetworksHandler(JSONHandler):
    fields = (
        "id",
        "name",
    )

    def PUT(self, cluster_id):
        web.header('Content-Type', 'application/json')
        cluster = orm().query(Cluster).get(cluster_id)
        if not cluster:
            return web.notfound()
        new_nets = NetworkGroup.validate_collection_update(web.data())
        if not new_nets:
            raise web.badrequest()
        task_manager = CheckNetworksTaskManager(cluster_id=cluster.id)
        task = task_manager.execute(new_nets)
        if task.status != 'error':
            nets_to_render = []
            error = False
            for ng in new_nets:
                ng_db = orm().query(NetworkGroup).get(ng['id'])
                for key, value in ng.iteritems():
                    setattr(ng_db, key, value)
                try:
                    ng_db.create_networks()
                    ng_db.cluster.add_pending_changes("networks")
                except Exception as exc:
                    err = str(exc)
                    update_task_status(
                        task.uuid,
                        status="error",
                        progress=100,
                        msg=err
                    )
                    logger.error(traceback.format_exc())
                    error = True
                    break
                nets_to_render.append(ng_db)

            if task.status == 'error':
                orm().rollback()
            else:
                orm().commit()

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
        cluster = orm().query(Cluster).get(cluster_id)
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
        cluster = orm().query(Cluster).get(cluster_id)
        if not cluster:
            return web.notfound()

        attrs = cluster.attributes
        if not attrs:
            raise web.internalerror("No attributes found!")

        data = Attributes.validate(web.data())

        for key, value in data.iteritems():
            setattr(attrs, key, value)
        cluster.add_pending_changes("attributes")

        orm().add(attrs)
        orm().commit()

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

    def GET(self, cluster_id):
        web.header('Content-Type', 'application/json')
        cluster = orm().query(Cluster).get(cluster_id)
        if not cluster:
            return web.notfound()

        attrs = cluster.release.attributes_metadata.get("editable")
        if not attrs:
            raise web.internalerror("No attributes found!")

        return json.dumps({"editable": attrs}, indent=4)

    def PUT(self, cluster_id):
        logger.debug('ClusterAttributesDefaultsHandler:'
                     ' PUT request with cluster_id %s' % cluster_id)
        web.header('Content-Type', 'application/json')
        cluster = orm().query(Cluster).get(cluster_id)
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
        orm().add(attrs)
        orm().commit()
        cluster.add_pending_changes("attributes")

        logger.debug('ClusterAttributesDefaultsHandler:'
                     ' editable attributes for cluster_id %s were reset'
                     ' to default' % cluster_id)
        return json.dumps(
            {
                "editable": attrs.editable
            },
            indent=4
        )
