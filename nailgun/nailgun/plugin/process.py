# -*- coding: utf-8 -*-

import traceback
import time
from multiprocessing import Queue, Process

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
            try:
                task_uuid = self.queue.get()
                self.plugin_manager.process(task_uuid)
            except Exception as exc:
                # TaskHelper.set_error(task_uuid, exc)
                logger.error(traceback.format_exc())
                time.sleep(2)
