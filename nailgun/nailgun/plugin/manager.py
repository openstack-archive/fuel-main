# -*- coding: utf-8 -*-

from nailgun.logger import logger
import nailgun.plugin.process
import socket
from nailgun.db import orm
from nailgun.api.models import Task, Plugin
import nailgun.plugin.fsm


class PluginManager(object):

    def __init__(self, db=None):
        self.db = db or orm()
        self.queue = nailgun.plugin.process.get_queue()

    def add_install_plugin_task(self, plugin_data):
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
            self.install_plugin(plugin_id, task_uuid)

    def install_plugin(self, plugin_id, task_uuid):
        plugin_db = self.db.query(Plugin).get(plugin_id)
        plugin = nailgun.plugin.fsm.PluginFSM(
            plugin_db.id,
            plugin_db.state_name, self.db)

        plugin.install()
        if plugin.is_error:
            self._set_error(task_uuid)

        plugin.initialize()
        if plugin.is_error:
            self._set_error(task_uuid)

        plugin.run()

    def _set_error(self, task_uuid):
        pass

    def get_free_port():
        pass
        # get all plugin ports from db
        # get first port in range
        # check port is available
        # return port
