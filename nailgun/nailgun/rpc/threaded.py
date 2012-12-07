# -*- coding: utf-8 -*-

import time
import Queue
import types
import logging
import threading
import itertools

import greenlet
import eventlet
from sqlalchemy.orm import scoped_session, sessionmaker

import nailgun.rpc as rpc
from nailgun.db import Query
from nailgun.api.models import engine, Node, Network
from nailgun.api.models import Task
from nailgun.notifier import notifier

logger = logging.getLogger(__name__)
rpc_queue = Queue.Queue()


class TaskNotFound(Exception):
    pass


class NailgunReceiver(object):
    db = scoped_session(
        sessionmaker(bind=engine, query_cls=Query)
    )

    @classmethod
    def __update_task_status(cls, uuid, status, progress, msg=""):
        task = cls.db.query(Task).filter_by(uuid=uuid).first()
        if not task:
            logger.error("Can't set status='%s', message='%s':no task \
                    with UUID %s found!", status, msg, uuid)
            return
        previous_status = task.status
        data = {'status': status, 'progress': progress, 'message': msg}
        for key, value in data.iteritems():
            if value:
                setattr(task, key, value)
        cls.db.add(task)
        cls.db.commit()
        if previous_status != status:
            cls.__update_cluster_status(task)
        if task.parent:
            cls.__update_parent_task(task.parent)

    @classmethod
    def __update_parent_task(cls, task):
        subtasks = task.subtasks
        if len(subtasks):
            if all(map(lambda s: s.status == 'ready', subtasks)):
                task.status = 'ready'
                task.progress = 100
                cls.__update_cluster_status(task)
            elif all(map(lambda s: s.status == 'ready' or
                         s.status == 'error', subtasks)):
                task.status = 'error'
                task.progress = 100
                task.message = '; '.join(map(
                    lambda s: s.message, filter(
                        lambda s: s.status == 'error', subtasks)))
                cls.__update_cluster_status(task)
            else:
                total_progress = 0
                subtasks_with_progress = 0
                for subtask in subtasks:
                    if subtask.progress is not None:
                        subtasks_with_progress += 1
                        progress = subtask.progress
                        if subtask.status == 'ready':
                            progress = 100
                        total_progress += progress
                if subtasks_with_progress:
                    total_progress /= subtasks_with_progress
                task.progress = total_progress
            cls.db.add(task)
            cls.db.commit()

    @classmethod
    def __update_cluster_status(cls, task):
        # FIXME: should be moved to task/manager "finish" method after
        # web.ctx.orm issue is addressed
        if task.name == 'deploy':
            cluster = task.cluster
            if task.status == 'ready':
                # FIXME: we should also calculate deployment "validity"
                # (check if all of the required nodes of required roles are
                # present). If cluster is not "valid", we should also set
                # its status to "error" even if it is deployed successfully.
                # This method is also would be affected by web.ctx.orm issue.
                cluster.status = 'operational'
            elif task.status == 'error':
                cluster.status = 'error'
            cls.db.add(cluster)
            cls.db.commit()

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
            node_db = cls.db.query(Node).get(node['uid'])
            if not node_db:
                logger.error(
                    "Failed to delete node '%s': node doesn't exist", str(node)
                )
                break
            cls.db.delete(node_db)

        for node in error_nodes:
            node_db = cls.db.query(Node).get(node['uid'])
            if not node_db:
                logger.error(
                    "Failed to delete node '%s' marked as error from Naily:"
                    " node doesn't exist", str(node)
                )
                break
            node_db.pending_deletion = False
            node_db.status = 'error'
            cls.db.add(node_db)
        cls.db.commit()

        cls.__update_task_status(task_uuid, status, progress, error_msg)

    @classmethod
    def remove_cluster_resp(cls, **kwargs):
        task_uuid = kwargs.get('task_uuid')

        cls.remove_nodes_resp(**kwargs)

        task = cls.db.query(Task).filter_by(uuid=task_uuid).first()
        cluster = task.cluster

        if task.status in ('ready',):
            logger.debug("Removing cluster itself")
            cluster_name = cluster.name
            cls.db.delete(cluster)
            cls.db.commit()

            notifier.notify(
                "done",
                "Installation '%s' and all its nodes are deleted" % (
                    cluster_name),
                db=cls.db
            )

        elif task.status in ('error',):
            notifier.notify(
                "error",
                task.message,
                cluster.id,
                cls.db
            )

    @classmethod
    def deploy_resp(cls, **kwargs):
        logger.info("RPC method deploy_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes') or []
        message = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        error_nodes = []
        for node in nodes:
            # TODO if not found? or node['uid'] not specified?
            node_db = cls.db.query(Node).get(node['uid'])
            modified = False
            for param in ('status', 'progress'):
                if node.get(param):
                    setattr(node_db, param, node[param])
                    modified = True
            if modified:
                cls.db.add(node_db)
                cls.db.commit()
            if node.get('status') and node['status'] == 'error':
                error_nodes.append(node_db)

        if error_nodes:
            nodes_info = [
                unicode({
                    "MAC": n.mac,
                    "IP": n.ip or "Unknown",
                    "NAME": n.name or "Unknown"
                }) for n in error_nodes
            ]
            message = "Failed to deploy nodes:\n%s" % "\n".join(nodes_info)
            status = 'error'

        task = cls.db.query(Task).filter_by(uuid=task_uuid).first()

        if status in ('error',):
            notifier.notify(
                "error",
                message,
                task.cluster_id,
                cls.db
            )

        elif status in ('ready',):
            message = "Deployment of installation '%s' is done. \
                Access WebUI of OpenStack at http://here will \
                be the address" % task.cluster.name
            notifier.notify(
                "done",
                message,
                task.cluster_id,
                cls.db
            )
        cls.__update_task_status(task_uuid, status, progress, message)

    @classmethod
    def verify_networks_resp(cls, **kwargs):
        logger.info("RPC method verify_networks_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes')
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        # We simply check that each node received all vlans for cluster
        task = cls.db.query(Task).filter_by(uuid=task_uuid).first()
        if not task:
            logger.error("verify_networks_resp: task \
                    with UUID %s not found!", task_uuid)
            return
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
                    error_msg = 'Received empty node list from orchestrator.'
            else:
                nets_db = cls.db.query(Network).filter_by(
                    cluster_id=task.cluster_id
                ).all()
                vlans_db = [net.vlan_id for net in nets_db]
                iface_db = {'iface': 'eth0', 'vlans': set(vlans_db)}
                error_nodes = []
                for n in nodes:
                    # Now - for all interfaces (eth0, eth1, etc.)
                    for iface in n['networks']:
                        if iface['iface'] == iface_db['iface']:
                            absent_vlans = list(
                                iface_db['vlans'] - set(iface['vlans']))
                            if absent_vlans:
                                error_nodes.append(
                                    "uid: %r, interface: %s,"
                                    " absent vlans: %s" %
                                    (n['uid'],
                                    iface['iface'],
                                    absent_vlans)
                                )
                if error_nodes:
                    error_msg = "Following nodes have"\
                        " network errors:\n%s." % (
                        '; '.join(error_nodes))
                    logger.error(error_msg)
                    status = 'error'
        else:
            error_msg = (error_msg or
                         'verify_networks_resp: argument "nodes"'
                         ' have incorrect type')
            status = 'error'
            logger.error(error_msg)

        cls.__update_task_status(task_uuid, status, progress, error_msg)


class RPCThread(threading.Thread):
    def __init__(self):
        super(RPCThread, self).__init__()
        self.queue = rpc_queue
        self.db = scoped_session(
            sessionmaker(bind=engine, query_cls=Query)
        )
        self.receiver = NailgunReceiver()
        self.conn = rpc.create_connection(True)
        self.conn.create_consumer('nailgun', self.receiver)

    def run(self):
        logger.info("Starting RPC thread...")
        self.running = True
        # TODO: implement fail-safe auto-reloading
        self.conn.consume()
        self.conn.close()
