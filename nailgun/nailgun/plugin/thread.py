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

import traceback
import time
from sqlalchemy import update
import threading
from Queue import Queue

from nailgun.api.models import Task
from nailgun.task.helpers import TaskHelper
from nailgun.logger import logger
from nailgun.db import db

PLUGIN_PROCESSING_QUEUE = None


def get_queue():
    global PLUGIN_PROCESSING_QUEUE
    if not PLUGIN_PROCESSING_QUEUE:
        PLUGIN_PROCESSING_QUEUE = Queue()

    return PLUGIN_PROCESSING_QUEUE


class PluginThread(threading.Thread):
    """
    Separate thread. When plugin added in the queue
    thread started to processing plugin
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.db = db()
        self.queue = get_queue()

        from nailgun.plugin.manager import PluginManager
        self.plugin_manager = PluginManager()

    def soft_stop(self):
        self._stop.set()

    @property
    def stopped(self):
        return self._stop.isSet()

    def run(self):
        while not self.stopped:
            task_uuid = None
            try:
                if not self.queue.empty():
                    task_uuid = self.queue.get_nowait()
                    self.plugin_manager.process(task_uuid)
            except Exception as exc:
                if task_uuid:
                    self.set_error(task_uuid, exc)
                logger.error(traceback.format_exc())

            if self.queue.empty():
                time.sleep(1)

    def set_error(self, task_uuid, msg):
        self.db.query(Task).filter_by(uuid=task_uuid).update({
            'status': 'error',
            'progress': 100,
            'message': str(msg)})
        self.db.commit()
