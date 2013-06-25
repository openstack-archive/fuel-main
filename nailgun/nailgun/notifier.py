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

import json
import web
from datetime import datetime

from nailgun.db import orm
from nailgun.logger import logger
from nailgun.api.models import Notification, Task


class Notifier(object):

    def notify(self, topic, message,
               cluster_id=None, node_id=None, task_uuid=None):
        if topic == 'discover' and node_id is None:
            raise Exception("No node id in discover notification")
        task = None
        if task_uuid:
            task = orm().query(Task).filter_by(uuid=task_uuid).first()

        exist = None
        if node_id and task:
            exist = orm().query(Notification).filter_by(
                node_id=node_id,
                message=message,
                task=task
            ).first()

        if not exist:
            notification = Notification()
            notification.topic = topic
            notification.message = message
            notification.cluster_id = cluster_id
            notification.node_id = node_id
            if task:
                notification.task_id = task.id
            notification.datetime = datetime.now()
            orm().add(notification)
            orm().commit()
            logger.info(
                "Notification: topic: %s message: %s" % (topic, message)
            )


notifier = Notifier()
