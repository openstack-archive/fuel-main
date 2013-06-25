# -*- coding: utf-8 -*-

import nailgun.plugin.process
import nailgun.plugin.fsm

from nailgun.errors import errors
from nailgun.logger import logger
from nailgun.api.models import Task, Plugin
from nailgun.db import orm


class PluginManager(object):

    def __init__(self, db=None):
        self.db = db or orm()
        self.queue = nailgun.plugin.process.get_queue()

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
        plugin = nailgun.plugin.fsm.PluginFSM(
            plugin_db.id,
            plugin_db.state_name, self.db)

        plugin.install()
        if plugin.is_error:
            raise errors.PluginDownloading()

        plugin.initialize()
        if plugin.is_error:
            raise errors.PluginInitialization()

        plugin.run()
