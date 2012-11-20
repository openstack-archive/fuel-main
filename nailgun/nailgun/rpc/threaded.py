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
    def __update_task_status(cls, uuid, status, progress, error=""):
        task = cls.db.query(Task).filter_by(uuid=uuid).first()
        if not task:
            logger.error("Can't set status='%s', error='%s':no task \
                    with UUID %s found!", status, error, uuid)
            return
        data = {'status': status, 'progress': progress, 'error': error}
        for key, value in data.iteritems():
            if value:
                setattr(task, key, value)
        cls.db.add(task)
        cls.db.commit()
        if task.parent:
            cls.__update_parent_task(task.parent)

    @classmethod
    def __update_parent_task(cls, task):
        subtasks = task.subtasks
        if len(subtasks):
            if all(map(lambda s: s.status == 'ready', subtasks)):
                task.status = 'ready'
                task.progress = 100
            elif all(map(lambda s: s.status == 'ready' or
                         s.status == 'error', subtasks)):
                task.status = 'error'
                task.progress = 100
                task.error = '; '.join(map(
                    lambda s: s.error, filter(
                        lambda s: s.status == 'error', subtasks)))
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
    def deploy_resp(cls, **kwargs):
        logger.info("RPC method deploy_resp received: %s" % kwargs)
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes') or []
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        error_nodes = []
        for node in nodes:
            # TODO if not found? or node['uid'] not specified?
            node_db = cls.db.query(Node).get(node['uid'])
            if node.get('status'):
                node_db.status = node['status']
                cls.db.add(node_db)
                cls.db.commit()
                if node['status'] == 'error':
                    error_nodes.append(node_db)

        if error_nodes:
            nodes_info = [
                unicode({
                    "MAC": n.mac,
                    "IP": n.ip or "Unknown",
                    "NAME": n.name or "Unknown"
                }) for n in error_nodes
            ]
            error_msg = "Failed to deploy nodes:\n%s" % "\n".join(nodes_info)
            status = 'error'

        task = cls.db.query(Task).filter_by(uuid=task_uuid).first()

        if status in ('error',):
            notifier.notify(
                "error",
                error_msg,
                task.cluster_id,
                cls.db
            )

        elif status in ('ready',):
            notifier.notify(
                "done",
                "Deployment is done",
                task.cluster_id,
                cls.db
            )

        cls.__update_task_status(task_uuid, status, progress, error_msg)

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
        if not isinstance(nodes, (list, types.NoneType)) or len(nodes) == 0:
            status = 'error'
            if not error_msg:
                error_msg = 'Received empty node list from orchestrator.'

        if nodes is not None:
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
                                "uid: %r, interface: %s, absent vlans: %s" %
                                (n['uid'],
                                iface['iface'],
                                absent_vlans)
                            )
            if error_nodes:
                error_msg = "Following nodes have network errors:\n%s." % (
                    '; '.join(error_nodes))
                logger.error(error_msg)
                status = 'error'

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
