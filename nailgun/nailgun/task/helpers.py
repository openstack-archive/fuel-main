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

import os
import shutil
import logging

from nailgun.db import orm
from nailgun.logger import logger
from nailgun.api.models import Task
from nailgun.api.models import IPAddr
from nailgun.api.models import Node
from nailgun.settings import settings
from nailgun.network.manager import NetworkManager


class TaskHelper(object):

    @classmethod
    def make_slave_name(cls, nid, role):
        return u"%s-%s" % (role, str(nid))

    @classmethod
    def make_slave_fqdn(cls, nid, role):
        return u"%s.%s" % (cls.make_slave_name(nid, role), settings.DNS_DOMAIN)

    @classmethod
    def update_slave_nodes_fqdn(cls, nodes):
        for n in nodes:
            fqdn = cls.make_slave_fqdn(n.id, n.role)
            if n.fqdn != fqdn:
                n.fqdn = fqdn
                logger.debug("Updating node fqdn: %s %s", n.id, n.fqdn)
                orm().commit()

    @classmethod
    def prepare_syslog_dir(cls, node, prefix=None):
        logger.debug("Preparing syslog directories for node: %s", node.fqdn)
        if not prefix:
            prefix = settings.SYSLOG_DIR
        logger.debug("prepare_syslog_dir prefix=%s", prefix)

        old = os.path.join(prefix, str(node.ip))
        bak = os.path.join(prefix, "%s.bak" % str(node.fqdn))
        new = os.path.join(prefix, str(node.fqdn))

        netmanager = NetworkManager()
        admin_net_id = netmanager.get_admin_network_id()
        links = map(
            lambda i: os.path.join(prefix, i.ip_addr),
            orm().query(IPAddr.ip_addr).
            filter_by(node=node.id).
            filter_by(network=admin_net_id).all()
        )

        logger.debug("prepare_syslog_dir old=%s", old)
        logger.debug("prepare_syslog_dir new=%s", new)
        logger.debug("prepare_syslog_dir bak=%s", bak)
        logger.debug("prepare_syslog_dir links=%s", str(links))

        # backup directory if it exists
        if os.path.isdir(new):
            logger.debug("New %s already exists. Trying to backup", new)
            if os.path.islink(bak):
                logger.debug("Bak %s already exists and it is link. "
                             "Trying to unlink", bak)
                os.unlink(bak)
            elif os.path.isdir(bak):
                logger.debug("Bak %s already exists and it is directory. "
                             "Trying to remove", bak)
                shutil.rmtree(bak)
            os.rename(new, bak)

        # rename bootstrap directory into fqdn
        if os.path.islink(old):
            logger.debug("Old %s exists and it is link. "
                         "Trying to unlink", old)
            os.unlink(old)
        if os.path.isdir(old):
            logger.debug("Old %s exists and it is directory. "
                         "Trying to rename into %s", old, new)
            os.rename(old, new)
        else:
            logger.debug("Creating %s", new)
            os.makedirs(new)

        # creating symlinks
        for l in links:
            if os.path.islink(l) or os.path.isfile(l):
                logger.debug("%s already exists. "
                             "Trying to unlink", l)
                os.unlink(l)
            if os.path.isdir(l):
                logger.debug("%s already exists and it directory. "
                             "Trying to remove", l)
                shutil.rmtree(l)
            logger.debug("Creating symlink %s -> %s", l, new)
            os.symlink(str(node.fqdn), l)

        os.system("/usr/bin/pkill -HUP rsyslog")

    @classmethod
    def update_task_status(cls, uuid, status, progress, msg="", result=None):
        logger.debug("Updating task: %s", uuid)
        db = orm()
        task = db.query(Task).filter_by(uuid=uuid).first()
        if not task:
            logger.error("Can't set status='%s', message='%s':no task \
                    with UUID %s found!", status, msg, uuid)
            return
        previous_status = task.status
        data = {'status': status, 'progress': progress,
                'message': msg, 'result': result}
        for key, value in data.iteritems():
            if value is not None:
                setattr(task, key, value)
                logger.info(
                    u"Task {0} {1} is set to {2}".format(
                        task.uuid,
                        key,
                        value
                    )
                )
        db.add(task)
        db.commit()

        if previous_status != status and task.cluster_id:
            cls.update_cluster_status(uuid)
        if task.parent:
            logger.debug("Updating parent task: %s", task.parent.uuid)
            cls.update_parent_task(task.parent.uuid)

    @classmethod
    def update_parent_task(cls, uuid):
        db = orm()
        task = db.query(Task).filter_by(uuid=uuid).first()
        subtasks = task.subtasks
        if len(subtasks):
            if all(map(lambda s: s.status == 'ready', subtasks)):
                task.status = 'ready'
                task.progress = 100
                task.message = '; '.join(map(
                    lambda s: s.message, filter(
                        lambda s: s.message is not None, subtasks)))
                db.add(task)
                db.commit()
                cls.update_cluster_status(uuid)
            elif all(map(lambda s: s.status in ('ready', 'error'), subtasks)):
                task.status = 'error'
                task.progress = 100
                task.message = '; '.join(map(
                    lambda s: s.message, filter(
                        lambda s: s.status == 'error', subtasks)))
                db.add(task)
                db.commit()
                cls.update_cluster_status(uuid)
            else:
                subtasks_with_progress = filter(
                    lambda s: s.progress is not None,
                    subtasks
                )
                if subtasks_with_progress:
                    task.progress = int(
                        round(
                            sum(
                                [s.weight * s.progress for s
                                 in subtasks_with_progress]
                            ) /
                            sum(
                                [s.weight for s
                                 in subtasks_with_progress]
                            ), 0)
                    )
                else:
                    task.progress = 0
                db.add(task)
                db.commit()

    @classmethod
    def update_cluster_status(cls, uuid):
        db = orm()
        task = db.query(Task).filter_by(uuid=uuid).first()
        # FIXME: should be moved to task/manager "finish" method after
        # web.ctx.orm issue is addressed
        cluster = task.cluster
        if task.name == 'deploy':
            if task.status == 'ready':
                # FIXME: we should also calculate deployment "validity"
                # (check if all of the required nodes of required roles are
                # present). If cluster is not "valid", we should also set
                # its status to "error" even if it is deployed successfully.
                # This method is also would be affected by web.ctx.orm issue.
                cls.__set_cluster_status(cluster, 'operational')
                cluster.clear_pending_changes()
            elif task.status == 'error':
                cls.__set_cluster_status(cluster, 'error')
        elif task.name == 'provision':
            if task.status == 'error':
                cls.__set_cluster_status(cluster, 'error')
        db.commit()

    @classmethod
    def __set_cluster_status(cls, cluster, new_state):
        logger.debug(
            "Updating cluster (%s) status: from %s to %s",
            cluster.full_name, cluster.status, new_state)
        cluster.status = new_state

    @classmethod
    def nodes_to_delete(cls, cluster):
        return filter(
            lambda n: any([
                n.pending_deletion,
                n.needs_redeletion
            ]),
            cluster.nodes
        )

    @classmethod
    def nodes_to_deploy(cls, cluster):
        return sorted(filter(
            lambda n: any([
                n.pending_addition,
                n.needs_reprovision,
                n.needs_redeploy
            ]),
            cluster.nodes
        ), key=lambda n: n.id)

    @classmethod
    def nodes_to_provision(cls, cluster):
        return sorted(filter(
            lambda n: any([
                n.pending_addition,
                n.needs_reprovision
            ]),
            cluster.nodes
        ), key=lambda n: n.id)

    @classmethod
    def set_error(cls, task_uuid, message):
        cls.update_task_status(
            task_uuid,
            status="error",
            progress=100,
            msg=str(message))
