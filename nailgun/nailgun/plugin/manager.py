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

from nailgun.plugin.thread import get_queue
from nailgun.plugin.fsm import PluginFSM

from nailgun.errors import errors
from nailgun.logger import logger
from nailgun.api.models import Task, Plugin
from nailgun.db import db


class PluginManager(object):

    def __init__(self):
        self.db = db()
        self.queue = get_queue()

    def add_install_plugin_task(self, plugin_data):
        # TODO: check if plugin already installed
        plugin = Plugin(
            version=plugin_data['version'],
            name=plugin_data['name'],
            type=plugin_data['type'])
        self.db.add(plugin)
        self.db.commit()

        task = Task(name='install_plugin', cache={'plugin_id': plugin.id})
        self.db.add(task)
        self.db.commit()

        self.queue.put(task.uuid)
        return task

    def process(self, task_uuid):
        task = self.db.query(Task).filter_by(uuid=task_uuid).first()
        plugin_id = task.cache['plugin_id']

        if task.name == 'install_plugin':
            self.install_plugin(plugin_id)

    def install_plugin(self, plugin_id):
        plugin_db = self.db.query(Plugin).get(plugin_id)
        plugin = PluginFSM(plugin_db.id, plugin_db.state, self.db)

        plugin.install()
        if plugin.is_error:
            raise errors.PluginDownloading()

        plugin.initialize()
        if plugin.is_error:
            raise errors.PluginInitialization()

        plugin.run()
