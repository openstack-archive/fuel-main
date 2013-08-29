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


from nailgun.api.models import Task
from nailgun.plugin.thread import get_queue
from nailgun.plugin.thread import PluginThread
from nailgun.test.base import BaseHandlers


class TestPluginProcess(BaseHandlers):
    def setUp(self):
        super(TestPluginProcess, self).setUp()
        self.plugin_thread = PluginThread()
        self.plugin_thread.start()

    def tearDown(self):
        super(TestPluginProcess, self).tearDown()
        self.plugin_thread.soft_stop()

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
