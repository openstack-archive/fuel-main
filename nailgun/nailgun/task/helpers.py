# -*- coding: utf-8 -*-

import logging

from nailgun.db import orm
from nailgun.logger import logger
from nailgun.api.models import Task


def update_task_status(uuid, status, progress, msg="", result=None):
    task = orm().query(Task).filter_by(uuid=uuid).first()
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
    orm().add(task)
    orm().commit()
    if previous_status != status:
        update_cluster_status(uuid)
    if task.parent:
        update_parent_task(task.parent.uuid)


def update_parent_task(uuid):
    task = orm().query(Task).filter_by(uuid=uuid).first()
    subtasks = task.subtasks
    if len(subtasks):
        if all(map(lambda s: s.status == 'ready', subtasks)):
            task.status = 'ready'
            task.progress = 100
            task.message = '; '.join(map(
                lambda s: s.message, filter(
                    lambda s: s.message is not None, subtasks)))
            orm().add(task)
            orm().commit()
            update_cluster_status(uuid)
        elif all(map(lambda s: s.status in ('ready', 'error'), subtasks)):
            task.status = 'error'
            task.progress = 100
            task.message = '; '.join(map(
                lambda s: s.message, filter(
                    lambda s: s.status == 'error', subtasks)))
            orm().add(task)
            orm().commit()
            update_cluster_status(uuid)
        else:
            subtasks_with_progress = filter(
                lambda s: s.progress is not None,
                subtasks
            )
            if subtasks_with_progress:
                task.progress = int(float(sum(
                    [s.progress for s in subtasks_with_progress]
                )) / len(subtasks_with_progress))
            else:
                task.progress = 0
            orm().add(task)
            orm().commit()


def update_cluster_status(uuid):
    task = orm().query(Task).filter_by(uuid=uuid).first()
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
            cluster.clear_pending_changes()
        elif task.status == 'error':
            cluster.status = 'error'
        orm().add(cluster)
        orm().commit()
