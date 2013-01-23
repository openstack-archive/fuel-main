# -*- coding: utf-8 -*-

import json
import web
from datetime import datetime

from nailgun.db import orm
from nailgun.logger import logger
from nailgun.api.models import Notification, Task


class Notifier(object):

    def notify(self, topic, message,
               cluster_id=None, node_id=None, task_uuid=None):
        db = orm()
        exist = False
        if topic == 'discover' and node_id is None:
            raise Exception("No node id in discover notification")
        task = None
        if task_uuid:
            task = db.query(Task).filter_by(uuid=task_uuid).first()

        if node_id and task:
            exist = db.query(Notification).filter_by(
                node_id=node_id,
                message=message,
                task=task
            ).first()
            logger.info(exist)

        if not exist:
            notification = Notification()
            notification.topic = topic
            notification.message = message
            notification.cluster_id = cluster_id
            notification.node_id = node_id
            if task:
                notification.task_id = task.id
            notification.datetime = datetime.now()
            db.add(notification)
            db.commit()
            logger.info(
                "Notification: topic: %s message: %s" % (topic, message)
            )


notifier = Notifier()
