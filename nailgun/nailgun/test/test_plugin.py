# -*- coding: utf-8 -*-
from nailgun.test.base import BaseHandlers
from nailgun.plugin.process import get_queue, PluginProcessor
from nailgun.api.models import Task

class TestPluginProcess(BaseHandlers):
    def setUp(self):
        super(TestPluginProcess, self).setUp()
        self.plugin_processor = PluginProcessor()
        self.plugin_processor.start()

    def tearDown(self):
        super(TestPluginProcess, self).tearDown()
        self.plugin_processor.terminate()

    def test_task_set_to_error_when_exception_raised(self):
        queue = get_queue()
        task = Task(name='install_plugin', cache={'plugin_id': -1})
        self.env.db.add(task)
        self.env.db.commit()

        queue.put(task.uuid)

        def check_task_status_is_error():
            self.env.db.refresh(task)
            return task.status == 'error'

        self.env.wait_for_true(check_task_status_is_error, timeout=2)
        self.assertEquals(task.progress, 100)
