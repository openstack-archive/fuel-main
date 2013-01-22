# -*- coding: utf-8 -*-

import json
import web
from datetime import datetime

from nailgun.db import orm
from nailgun.logger import logger
from nailgun.api.models import Notification


class Notifier(object):

    def notify(self, topic, message, cluster_id=None, node_id=None, task_id=None):
        db = orm()
        exist = False
        if topic == 'discover' and node_id is None:
            raise Exception("No node id in discover notification")
        if node_id and task_id:
            exist = db.query(Notification).filter_by(
                node_id=node_id,
                task_id=task_id,
                message=message
            ).first()
        
        if not exist:
            notification = Notification()
            notification.topic = topic
            notification.message = message
            notification.cluster_id = cluster_id
            notification.node_id = node_id
            notification.task_id = task_id
            notification.datetime = datetime.now()
            db.add(notification)
            db.commit()
            logger.info("Notification: topic: %s message: %s" % (topic, message))


notifier = Notifier()
