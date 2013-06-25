# -*- coding: utf-8 -*-

import traceback
import time
from multiprocessing import Queue, Process
from sqlalchemy import update

from nailgun.api.models import Task
from nailgun.task.helpers import TaskHelper
from nailgun.logger import logger
from nailgun.db import make_session
import nailgun.plugin.manager

PLUGIN_PROCESSING_QUEUE = None

def get_queue():
    global PLUGIN_PROCESSING_QUEUE
    if not PLUGIN_PROCESSING_QUEUE:
        PLUGIN_PROCESSING_QUEUE = Queue()

    return PLUGIN_PROCESSING_QUEUE

class PluginProcessor(Process):
    def __init__(self):
    	Process.__init__(self)
        self.db = make_session()
        self.plugin_manager = nailgun.plugin.manager.PluginManager(self.db)
    	self.queue = get_queue()

    def run(self):
        while True:
            task_uuid = None
            try:
                task_uuid = self.queue.get()
                self.plugin_manager.process(task_uuid)
            except Exception as exc:
                if task_uuid:
                    self.set_error(task_uuid, exc)
                logger.error(traceback.format_exc())
                time.sleep(2)

    def set_error(self, task_uuid, msg):
        self.db.query(Task).filter_by(uuid=task_uuid).update({
            'status': 'error',
            'progress': 100,
            'msg': str(msg)})
