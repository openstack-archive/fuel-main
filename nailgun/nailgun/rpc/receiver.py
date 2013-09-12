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

import collections
import itertools
import json
import netifaces
import os
import traceback


from sqlalchemy import or_

from nailgun.api.models import IPAddr
from nailgun.api.models import Node
from nailgun.api.models import Release
from nailgun.api.models import Task
from nailgun.db import db
from nailgun.logger import logger
from nailgun.network.manager import NetworkManager
from nailgun import notifier
from nailgun.settings import settings
from nailgun.task.helpers import TaskHelper


class TaskNotFound(Exception):
    pass


class NailgunReceiver(object):

    @classmethod
    def remove_nodes_resp(cls, **kwargs):
        logger.info(
            "RPC method remove_nodes_resp received: %s" %
            json.dumps(kwargs)
        )
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes') or []
        error_nodes = kwargs.get('error_nodes') or []
        inaccessible_nodes = kwargs.get('inaccessible_nodes') or []
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        for node in nodes:
            node_db = db().query(Node).get(node['uid'])
            if not node_db:
                logger.error(
                    u"Failed to delete node '%s': node doesn't exist",
                    str(node)
                )
                break
            db().delete(node_db)

        for node in inaccessible_nodes:
            # Nodes which not answered by rpc just removed from db
            node_db = db().query(Node).get(node['uid'])
            if node_db:
                logger.warn(
                    u'Node %s not answered by RPC, removing from db',
                    node_db.human_readable_name)
                db().delete(node_db)

        for node in error_nodes:
            node_db = db().query(Node).get(node['uid'])
            if not node_db:
                logger.error(
                    u"Failed to delete node '%s' marked as error from Naily:"
                    " node doesn't exist", str(node)
                )
                break
            node_db.pending_deletion = False
            node_db.status = 'error'
            db().add(node_db)
            node['name'] = node_db.name
        db().commit()

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
                ', '.join(
                    [n.get('name') or "ID: {0}".format(n['uid'])
                        for n in error_nodes])
            )
            notifier.notify("error", err_msg)
        if not error_msg:
            error_msg = ". ".join([success_msg, err_msg])

        TaskHelper.update_task_status(task_uuid, status, progress, error_msg)

    @classmethod
    def remove_cluster_resp(cls, **kwargs):
        network_manager = NetworkManager()
        logger.info(
            "RPC method remove_cluster_resp received: %s" %
            json.dumps(kwargs)
        )
        task_uuid = kwargs.get('task_uuid')

        cls.remove_nodes_resp(**kwargs)

        task = db().query(Task).filter_by(uuid=task_uuid).first()
        cluster = task.cluster

        if task.status in ('ready',):
            logger.debug("Removing environment itself")
            cluster_name = cluster.name

            nws = itertools.chain(
                *[n.networks for n in cluster.network_groups]
            )
            ips = db().query(IPAddr).filter(
                IPAddr.network.in_([n.id for n in nws])
            )
            map(db().delete, ips)
            db().commit()

            db().delete(cluster)
            db().commit()

            # Dmitry's hack for clearing VLANs without networks
            network_manager.clear_vlans()

            notifier.notify(
                "done",
                u"Environment '%s' and all its nodes are deleted" % (
                    cluster_name
                )
            )

        elif task.status in ('error',):
            cluster.status = 'error'
            db().add(cluster)
            db().commit()
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
        logger.info(
            "RPC method deploy_resp received: %s" %
            json.dumps(kwargs)
        )
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes') or []
        message = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        task = db().query(Task).filter_by(uuid=task_uuid).first()
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

        # First of all, let's update nodes in database
        for node in nodes:
            node_db = db().query(Node).get(node['uid'])

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

            db().add(node_db)
            db().commit()

        # We should calculate task progress by nodes info
        task = db().query(Task).filter_by(uuid=task_uuid).first()
        coeff = settings.PROVISIONING_PROGRESS_COEFF or 0.3
        if nodes and not progress:
            nodes_progress = []
            nodes_db = db().query(Node).filter_by(
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
            cls._error_action(task, status, progress, message)
        elif status in ('ready',):
            cls._success_action(task, status, progress)
        else:
            TaskHelper.update_task_status(task.uuid, status, progress, message)

    @classmethod
    def provision_resp(cls, **kwargs):
        # For now provision task is nothing more than just adding
        # system into cobbler and rebooting node. Then we think task
        # is ready. We don't wait for end of node provisioning.
        logger.info(
            "RPC method provision_resp received: %s" %
            json.dumps(kwargs)
        )
        task_uuid = kwargs.get('task_uuid')
        message = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        task = db().query(Task).filter_by(uuid=task_uuid).first()
        if not task:
            logger.warning(u"No task with uuid %s found", task_uuid)
            return

        TaskHelper.update_task_status(task.uuid, status, progress, message)

    @classmethod
    def _generate_error_message(cls, task, error_types, names_only=False):
        nodes_info = []
        error_nodes = db().query(Node).filter_by(
            cluster_id=task.cluster_id
        ).filter(
            or_(
                Node.status == 'error',
                Node.online == (False)
            )
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
    def _error_action(cls, task, status, progress, message=None):
        if message:
            message = u"Deployment has failed. {0}".format(message)
        else:
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
        TaskHelper.update_task_status(task.uuid, status, progress, message)

    @classmethod
    def _success_action(cls, task, status, progress):
        network_manager = NetworkManager()
        # check if all nodes are ready
        if any(map(lambda n: n.status == 'error',
                   task.cluster.nodes)):
            cls._error_action(task, 'error', 100)
            return

        if task.cluster.mode in ('singlenode', 'multinode'):
            # determining horizon url - it's an IP
            # of a first cluster controller
            controller = db().query(Node).filter_by(
                cluster_id=task.cluster_id
            ).filter(Node.role_list.any(name='controller')).first()
            if controller:
                logger.debug(
                    u"Controller is found, node_id=%s, "
                    "getting it's IP addresses",
                    controller.id
                )
                public_net = filter(
                    lambda n: n['name'] == 'public' and 'ip' in n,
                    network_manager.get_node_networks(controller.id)
                )
                if public_net:
                    horizon_ip = public_net[0]['ip'].split('/')[0]
                    message = (
                        u"Deployment of environment '{0}' is done. "
                        "Access the OpenStack dashboard (Horizon) at "
                        "http://{1}/ or via internal network at http://{2}/"
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
                logger.warning(u"Controller node not found in '{0}'".format(
                    task.cluster.name
                ))
        elif task.cluster.is_ha_mode:
            # determining horizon url in HA mode - it's vip
            # from a public network saved in task cache
            try:
                netmanager = NetworkManager()
                message = (
                    u"Deployment of environment '{0}' is done. "
                    "Access the OpenStack dashboard (Horizon) at {1}"
                ).format(
                    task.cluster.name,
                    netmanager.get_horizon_url(task.cluster.id)
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
        TaskHelper.update_task_status(task.uuid, status, progress, message)

    @classmethod
    def verify_networks_resp(cls, **kwargs):
        logger.info(
            "RPC method verify_networks_resp received: %s" %
            json.dumps(kwargs)
        )
        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes')
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        # We simply check that each node received all vlans for cluster
        task = db().query(Task).filter_by(uuid=task_uuid).first()
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
            cached_nodes = task.cache['args']['nodes']
            node_uids = [str(n['uid']) for n in nodes]
            cached_node_uids = [str(n['uid']) for n in cached_nodes]
            forgotten_uids = set(cached_node_uids) - set(node_uids)

            if forgotten_uids:
                absent_nodes = db().query(Node).filter(
                    Node.id.in_(forgotten_uids)
                ).all()
                absent_node_names = []
                for n in absent_nodes:
                    if n.name:
                        absent_node_names.append(n.name)
                    else:
                        absent_node_names.append('id: %s' % n.id)
                if not error_msg:
                    error_msg = 'Node(s) {0} didn\'t return data.'.format(
                        ', '.join(absent_node_names)
                    )
                status = 'error'
            elif len(nodes) < 2:
                status = 'error'
                if not error_msg:
                    error_msg = 'At least two nodes are required to be in '\
                                'the environment for network verification.'
            else:
                error_nodes = []
                for node in nodes:
                    cached_nodes_filtered = filter(
                        lambda n: str(n['uid']) == str(node['uid']),
                        cached_nodes
                    )

                    if not cached_nodes_filtered:
                        logger.warning(
                            "verify_networks_resp: arguments contain node "
                            "data which is not in the task cache: %r",
                            node
                        )
                        continue

                    cached_node = cached_nodes_filtered[0]

                    for cached_network in cached_node['networks']:
                        received_networks_filtered = filter(
                            lambda n: n['iface'] == cached_network['iface'],
                            node.get('networks', [])
                        )

                        if received_networks_filtered:
                            received_network = received_networks_filtered[0]
                            absent_vlans = list(
                                set(cached_network['vlans']) -
                                set(received_network['vlans'])
                            )
                        else:
                            logger.warning(
                                "verify_networks_resp: arguments don't contain"
                                " data for interface: uid=%s iface=%s",
                                node['uid'], cached_network['iface']
                            )
                            absent_vlans = cached_network['vlans']

                        if absent_vlans:
                            data = {'uid': node['uid'],
                                    'interface': received_network['iface'],
                                    'absent_vlans': absent_vlans}
                            node_db = db().query(Node).get(node['uid'])
                            if node_db:
                                data['name'] = node_db.name
                                db_nics = filter(
                                    lambda i:
                                    i.name == received_network['iface'],
                                    node_db.interfaces
                                )
                                if db_nics:
                                    data['mac'] = db_nics[0].mac
                                else:
                                    logger.warning(
                                        "verify_networks_resp: can't find "
                                        "interface %r for node %r in DB",
                                        received_network['iface'], node_db.id
                                    )
                                    data['mac'] = 'unknown'
                            else:
                                logger.warning(
                                    "verify_networks_resp: can't find node "
                                    "%r in DB",
                                    node['uid']
                                )

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

        TaskHelper.update_task_status(task_uuid, status,
                                      progress, error_msg, result)

    @classmethod
    def _master_networks_gen(cls, ifaces):
        for iface in ifaces:
            iface_data = netifaces.ifaddresses(iface)
            if netifaces.AF_LINK in iface_data:
                yield netifaces.ifaddresses(iface)[netifaces.AF_LINK]

    @classmethod
    def _get_master_macs(cls):
        return itertools.chain(*cls._master_networks_gen(
            netifaces.interfaces()))

    @classmethod
    def check_dhcp_resp(cls, **kwargs):
        """Receiver method for check_dhcp task
        For example of kwargs check FakeCheckingDhcpThread
        """
        logger.info(
            "RPC method check_dhcp_resp received: %s" %
            json.dumps(kwargs)
        )
        messages = []
        result = collections.defaultdict(list)
        message_template = ("Dhcp server on {server_id} - {mac}."
                            "Discovered from node {yiaddr} on {iface}.")

        task_uuid = kwargs.get('task_uuid')
        nodes = kwargs.get('nodes')
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        macs = [item['addr'] for item in cls._get_master_macs()]
        logger.debug('Mac addr on master node %s', macs)

        if nodes:
            for node in nodes:
                if node['status'] == 'ready':
                    for row in node.get('data', []):
                        if row['mac'] not in macs:
                            messages.append(message_template.format(**row))
                            result[node['uid']].append(row)
                elif node['status'] == 'error':
                    messages.append(node.get('error_msg',
                                             ('Dhcp check method failed.'
                                              ' Check logs for details.')))
            status = status if not messages else "error"
            error_msg = '\n'.join(messages) if messages else error_msg
        TaskHelper.update_task_status(task_uuid, status,
                                      progress, error_msg, result)

    # Red Hat related callbacks

    @classmethod
    def check_redhat_credentials_resp(cls, **kwargs):
        logger.info(
            "RPC method check_redhat_credentials_resp received: %s" %
            json.dumps(kwargs)
        )
        task_uuid = kwargs.get('task_uuid')
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        task = db().query(Task).filter_by(uuid=task_uuid).first()
        if not task:
            logger.error("check_redhat_credentials_resp: task \
                    with UUID %s not found!", task_uuid)
            return

        release_info = task.cache['args']['release_info']
        release_id = release_info['release_id']
        release = db().query(Release).get(release_id)
        if not release:
            logger.error("download_release_resp: Release"
                         " with ID %s not found", release_id)
            return

        if error_msg:
            status = 'error'
            cls._update_release_state(release_id, 'error')
            # TODO(NAME): remove this ugly checks
            if 'Unknown error' in error_msg:
                error_msg = 'Failed to check Red Hat ' \
                            'credentials'
            if error_msg != 'Task aborted':
                notifier.notify('error', error_msg)

        result = {
            "release_info": {
                "release_id": release_id
            }
        }

        TaskHelper.update_task_status(
            task_uuid,
            status,
            progress,
            error_msg,
            result
        )

    @classmethod
    def redhat_check_licenses_resp(cls, **kwargs):
        logger.info(
            "RPC method redhat_check_licenses_resp received: %s" %
            json.dumps(kwargs)
        )
        task_uuid = kwargs.get('task_uuid')
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')
        notify = kwargs.get('msg')

        task = db().query(Task).filter_by(uuid=task_uuid).first()
        if not task:
            logger.error("redhat_check_licenses_resp: task \
                    with UUID %s not found!", task_uuid)
            return

        release_info = task.cache['args']['release_info']
        release_id = release_info['release_id']
        release = db().query(Release).get(release_id)
        if not release:
            logger.error("download_release_resp: Release"
                         " with ID %s not found", release_id)
            return

        if error_msg:
            status = 'error'
            cls._update_release_state(release_id, 'error')
            # TODO(NAME): remove this ugly checks
            if 'Unknown error' in error_msg:
                error_msg = 'Failed to check Red Hat licenses '
            if error_msg != 'Task aborted':
                notifier.notify('error', error_msg)

        if notify:
            notifier.notify('error', notify)

        result = {
            "release_info": {
                "release_id": release_id
            }
        }

        TaskHelper.update_task_status(
            task_uuid,
            status,
            progress,
            error_msg,
            result
        )

    @classmethod
    def download_release_resp(cls, **kwargs):
        logger.info(
            "RPC method download_release_resp received: %s" %
            json.dumps(kwargs)
        )
        task_uuid = kwargs.get('task_uuid')
        error_msg = kwargs.get('error')
        status = kwargs.get('status')
        progress = kwargs.get('progress')

        task = db().query(Task).filter_by(uuid=task_uuid).first()
        if not task:
            logger.error("download_release_resp: task"
                         " with UUID %s not found", task_uuid)
            return

        release_info = task.cache['args']['release_info']
        release_id = release_info['release_id']
        release = db().query(Release).get(release_id)
        if not release:
            logger.error("download_release_resp: Release"
                         " with ID %s not found", release_id)
            return

        if error_msg:
            status = 'error'
            error_msg = "{0} download and preparation " \
                        "has failed.".format(release.name)
            cls._download_release_error(
                release_id,
                error_msg
            )
        elif progress == 100 and status == 'ready':
            cls._download_release_completed(release_id)

        result = {
            "release_info": {
                "release_id": release_id
            }
        }

        TaskHelper.update_task_status(
            task_uuid,
            status,
            progress,
            error_msg,
            result
        )

    @classmethod
    def _update_release_state(cls, release_id, state):
        release = db().query(Release).get(release_id)
        release.state = state
        db.add(release)
        db.commit()

    @classmethod
    def _download_release_completed(cls, release_id):
        release = db().query(Release).get(release_id)
        release.state = 'available'
        db().commit()
        success_msg = u"Successfully downloaded {0}".format(
            release.name
        )
        notifier.notify("done", success_msg)

    @classmethod
    def _download_release_error(
        cls,
        release_id,
        error_message
    ):
        release = db().query(Release).get(release_id)
        release.state = 'error'
        db().commit()
        # TODO(NAME): remove this ugly checks
        if error_message != 'Task aborted':
            notifier.notify('error', error_message)

    @classmethod
    def dump_environment_resp(cls, **kwargs):
        logger.info(
            "RPC method dump_environment_resp received: %s" %
            json.dumps(kwargs)
        )
        task_uuid = kwargs.get('task_uuid')
        status = kwargs.get('status')
        progress = kwargs.get('progress')
        error = kwargs.get('error')
        msg = kwargs.get('msg')
        if status == 'error':
            notifier.notify('error', error)
            TaskHelper.update_task_status(task_uuid, status, progress, error)
        elif status == 'ready':
            dumpfile = os.path.basename(msg)
            notifier.notify('done', 'Snapshot is ready. '
                            'Visit Support page to download')
            TaskHelper.update_task_status(
                task_uuid, status, progress,
                'http://{0}:8080/dump/{1}'.format(
                    settings.MASTER_IP, dumpfile))
