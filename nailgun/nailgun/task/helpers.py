import logging

from nailgun.db import orm
from nailgun.api.models import Task

logger = logging.getLogger(__name__)


def update_task_status(uuid, status, progress, msg="", db=None):
    db_orm = db or orm()
    task = db_orm.query(Task).filter_by(uuid=uuid).first()
    if not task:
        logger.error("Can't set status='%s', message='%s':no task \
                with UUID %s found!", status, msg, uuid)
        return
    previous_status = task.status
    data = {'status': status, 'progress': progress, 'message': msg}
    for key, value in data.iteritems():
        if value:
            setattr(task, key, value)
    db_orm.add(task)
    db_orm.commit()
    if previous_status != status:
        update_cluster_status(task, db_orm)
    if task.parent:
        update_parent_task(task.parent, db_orm)


def update_parent_task(task, db=None):
    db_orm = db or orm()
    subtasks = task.subtasks
    if len(subtasks):
        if all(map(lambda s: s.status == 'ready', subtasks)):
            task.status = 'ready'
            task.progress = 100
            task.message = '; '.join(map(
                lambda s: s.message, filter(
                    lambda s: s.message is not None, subtasks)))
            update_cluster_status(task, db_orm)
        elif all(map(lambda s: s.status == 'ready' or
                     s.status == 'error', subtasks)):
            task.status = 'error'
            task.progress = 100
            task.message = '; '.join(map(
                lambda s: s.message, filter(
                    lambda s: s.status == 'error', subtasks)))
            update_cluster_status(task, db_orm)
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
        db_orm.add(task)
        db_orm.commit()


def update_cluster_status(task, db=None):
    db_orm = db or orm()
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
        db_orm.add(cluster)
        db_orm.commit()
