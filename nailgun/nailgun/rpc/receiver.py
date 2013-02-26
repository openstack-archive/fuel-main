# -*- coding: utf-8 -*-

import time
import Queue
import types
import traceback
import itertools

import greenlet
import eventlet
from web.utils import ThreadedDict
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import or_

import nailgun.rpc as rpc
from nailgun.logger import logger
from nailgun.db import orm, engine
from nailgun.network.manager import get_node_networks
from nailgun.settings import settings
from nailgun.task.helpers import update_task_status
from nailgun.api.models import Node, Network, NetworkGroup
from nailgun.api.models import Task
from nailgun.notifier import notifier


class TaskNotFound(Exception):
    pass


class NailgunReceiver(object):

    @classmethod
    def remove_nodes_resp(cls, **kwargs):
        logger.info("RPC method remove_nodes_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes') or []
        error_nodes = kwargs.get('error_nodes') or []
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        for node in nodes:
            node_db = orm().query(Node).get(node['uid'])
            if not node_db:
                logger.error(
                    u"Failed to delete node '%s': node doesn't exist",
                    str(node)
                )
                break
            orm().delete(node_db)

        for node in error_nodes:
            node_db = orm().query(Node).get(node['uid'])
            if not node_db:
                logger.error(
                    u"Failed to delete node '%s' marked as error from Naily:"
                    " node doesn't exist", str(node)
                )
                break
            node_db.pending_deletion = False
            node_db.status = 'error'
            orm().add(node_db)
            node['name'] = node_db.name
        orm().commit()

        success_msg = u"No nodes were removed"
        err_msg = u"No errors occurred"
        if nodes:
            success_msg = u"Successfully removed {0} node(s)".format(
                len(nodes)
            )
            notifier.notify("done", success_msg)
        if error_nodes:
            err_msg = u"Failed to remove {0} node(s): {1}".format(
                len(error_nodes),
                ', '.join([n['name'] for n in error_nodes])
            )
            notifier.notify("error", err_msg)
        if not error_msg:
            error_msg = ". ".join([success_msg, err_msg])

        update_task_status(task_uuid, status, progress, error_msg)

    @classmethod
    def remove_cluster_resp(cls, **kwargs):
        logger.info("RPC method remove_cluster_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')

        cls.remove_nodes_resp(**kwargs)

        task = orm().query(Task).filter_by(uuid=task_uuid).first()
        cluster = task.cluster

        if task.status in ('ready',):
            logger.debug("Removing environment itself")
            cluster_name = cluster.name
            orm().delete(cluster)
            orm().commit()

            notifier.notify(
                "done",
                u"Environment '%s' and all its nodes are deleted" % (
                    cluster_name
                )
            )

        elif task.status in ('error',):
            cluster.status = 'error'
            orm().add(cluster)
            orm().commit()
            if not task.message:
                task.message = "Failed to delete nodes:\n{0}".format(
                    cls._generate_error_message(
                        task,
                        error_types=('deletion',)
                    )
                )
            notifier.notify(
                "error",
                task.message,
                cluster.id
            )

    @classmethod
    def deploy_resp(cls, **kwargs):
        logger.info("RPC method deploy_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes') or []
        message = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        task = orm().query(Task).filter_by(uuid=task_uuid).first()
        if not task:
            # No task found - nothing to do here, returning
            logger.warning(
                u"No task with uuid '{0}'' found - nothing changed".format(
                    task_uuid
                )
            )
            return
        if not status:
            status = task.status

        error_nodes = []
        # First of all, let's update nodes in database
        for node in nodes:
            node_db = orm().query(Node).get(node['uid'])

            if not node_db:
                logger.warning(
                    u"No node found with uid '{0}' - nothing changed".format(
                        node['uid']
                    )
                )
                continue

            update_fields = (
                'error_msg',
                'error_type',
                'status',
                'progress',
                'online'
            )
            for param in update_fields:
                if param in node:
                    logger.debug(
                        u"Updating node {0} - set {1} to {2}".format(
                            node['uid'],
                            param,
                            node[param]
                        )
                    )
                    setattr(node_db, param, node[param])

                    if param == 'progress' and node.get('status') == 'error' \
                            or node.get('online') is False:
                        # If failure occurred with node
                        # it's progress should be 100
                        node_db.progress = 100
                        # Setting node error_msg for offline nodes
                        if node.get('online') is False \
                                and not node_db.error_msg:
                            node_db.error_msg = u"Node is offline"
                        # Notification on particular node failure
                        notifier.notify(
                            "error",
                            u"Failed to deploy node '{0}': {1}".format(
                                node_db.name,
                                node_db.error_msg or "Unknown error"
                            ),
                            cluster_id=task.cluster_id,
                            node_id=node['uid'],
                            task_uuid=task_uuid
                        )

            orm().add(node_db)
            orm().commit()

        # We should calculate task progress by nodes info
        coeff = settings.PROVISIONING_PROGRESS_COEFF or 0.3
        if nodes and not progress:
            nodes_progress = []
            nodes_db = orm().query(Node).filter_by(
                cluster_id=task.cluster_id).all()
            for node in nodes_db:
                if node.status == "discover":
                    nodes_progress.append(0)
                elif not node.online:
                    nodes_progress.append(100)
                elif node.status in ['provisioning', 'provisioned'] or \
                        node.needs_reprovision:
                    nodes_progress.append(float(node.progress) * coeff)
                elif node.status in ['deploying', 'ready'] or \
                        node.needs_redeploy:
                    nodes_progress.append(
                        100.0 * coeff + float(node.progress) * (1.0 - coeff)
                    )
            if nodes_progress:
                progress = int(
                    float(sum(nodes_progress)) / len(nodes_progress)
                )

        # Let's check the whole task status
        if status in ('error',):
            cls._error_action(task, status, progress)
        elif status in ('ready',):
            cls._success_action(task, status, progress)
        else:
            update_task_status(task.uuid, status, progress, message)

    @classmethod
    def _generate_error_message(cls, task, error_types, names_only=False):
        nodes_info = []
        error_nodes = orm().query(Node).filter_by(
            cluster_id=task.cluster_id
        ).filter(
            or_(Node.status == 'error', not Node.online)
        ).filter(
            Node.error_type.in_(error_types)
        ).all()
        for n in error_nodes:
            if names_only:
                nodes_info.append(
                    "'{0}'".format(n.name)
                )
            else:
                nodes_info.append(
                    u"'{0}': {1}".format(
                        n.name,
                        n.error_msg
                    )
                )
        if nodes_info:
            if names_only:
                message = u", ".join(nodes_info)
            else:
                message = u"\n".join(nodes_info)
        else:
            message = u"Unknown error"
        return message

    @classmethod
    def _error_action(cls, task, status, progress):
        message = u"Deployment has failed. Check these nodes:\n{0}".format(
            cls._generate_error_message(
                task,
                error_types=('deploy', 'provision'),
                names_only=True
            )
        )
        notifier.notify(
            "error",
            message,
            task.cluster_id
        )
        update_task_status(task.uuid, status, progress, message)

    @classmethod
    def _success_action(cls, task, status, progress):
        # check if all nodes are ready
        if any(map(lambda n: n.status == 'error',
                   task.cluster.nodes)):
            cls._error_action(task, 'error', 100)
            return

        if task.cluster.mode in ('singlenode', 'multinode'):
            # determining horizon url - it's an IP
            # of a first cluster controller
            controller = orm().query(Node).filter_by(
                cluster_id=task.cluster_id,
                role='controller'
            ).first()
            if controller:
                logger.debug(
                    u"Controller is found, node_id=%s, "
                    "getting it's IP addresses",
                    controller.id
                )
                public_net = filter(
                    lambda n: n['name'] == 'public' and 'ip' in n,
                    get_node_networks(controller.id)
                )
                if public_net:
                    horizon_ip = public_net[0]['ip'].split('/')[0]
                    message = (
                        u"Deployment of environment '{0}' is done. "
                        "Access WebUI of OpenStack at http://{1}/ or via "
                        "internal network at http://{2}/"
                    ).format(
                        task.cluster.name,
                        horizon_ip,
                        controller.ip
                    )
                else:
                    message = (
                        u"Deployment of environment '{0}' is done"
                    ).format(task.cluster.name)
                    logger.warning(
                        u"Public ip for controller node "
                        "not found in '{0}'".format(task.cluster.name)
                    )
            else:
                message = (
                    u"Deployment of environment"
                    " '{0}' is done"
                ).format(task.cluster.name)
                logger.warning("Controller node not found in '{0}'".format(
                    task.cluster.name
                ))
        elif task.cluster.mode == 'ha':
            # determining horizon url in HA mode - it's vip
            # from a public network saved in task cache
            args = task.cache.get('args')
            try:
                vip = args['attributes']['public_vip']
                message = (
                    u"Deployment of environment '{0}' is done. "
                    "Access WebUI of OpenStack at http://{1}/"
                ).format(
                    task.cluster.name,
                    vip
                )
            except Exception as exc:
                logger.error(": ".join([
                    str(exc),
                    traceback.format_exc()
                ]))
                message = (
                    u"Deployment of environment"
                    " '{0}' is done"
                ).format(task.cluster.name)
                logger.warning(
                    u"Cannot find virtual IP for '{0}'".format(
                        task.cluster.name
                    )
                )

        notifier.notify(
            "done",
            message,
            task.cluster_id
        )
        update_task_status(task.uuid, status, progress, message)

    @classmethod
    def verify_networks_resp(cls, **kwargs):
        logger.info("RPC method verify_networks_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes')
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        # We simply check that each node received all vlans for cluster
        task = orm().query(Task).filter_by(uuid=task_uuid).first()
        if not task:
            logger.error("verify_networks_resp: task \
                    with UUID %s not found!", task_uuid)
            return
        result = []
        #  We expect that 'nodes' contains all nodes which we test.
        #  Situation when some nodes not answered must be processed
        #  in orchestrator early.
        if nodes is None:
            # If no nodes in kwargs then we update progress or status only.
            pass
        elif isinstance(nodes, list):
            if len(nodes) == 0:
                status = 'error'
                if not error_msg:
                    error_msg = 'Deployment Orchestrator failed to perform ' \
                                'network connectivity check. ' \
                                'See logs for details.'
            else:
                vlans_sent = [
                    n['vlan_id'] for n in task.cache['args']['networks']
                ]
                iface_sent = {'iface': 'eth0', 'vlans': set(vlans_sent)}
                error_nodes = []
                for n in nodes:
                    # Now - for all interfaces (eth0, eth1, etc.)
                    for iface in n['networks']:
                        if iface['iface'] == iface_sent['iface']:
                            absent_vlans = list(
                                iface_sent['vlans'] - set(iface['vlans']))
                            if absent_vlans:
                                data = {'uid': n['uid'],
                                        'interface': iface['iface'],
                                        'absent_vlans': absent_vlans}
                                node_db = orm().query(Node).get(n['uid'])
                                if node_db:
                                    data.update({'name': node_db.name,
                                                 'mac': node_db.mac})
                                error_nodes.append(data)
                if error_nodes:
                    result = error_nodes
                    status = 'error'
        else:
            error_msg = (error_msg or
                         'verify_networks_resp: argument "nodes"'
                         ' have incorrect type')
            status = 'error'
            logger.error(error_msg)

        update_task_status(task_uuid, status, progress, error_msg, result)
