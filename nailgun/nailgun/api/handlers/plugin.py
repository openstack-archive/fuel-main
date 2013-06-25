# -*- coding: utf-8 -*-

import web
import json

from nailgun.api.handlers.base \
    import JSONHandler, content_json, build_json_response
from nailgun.plugin.manager import PluginManager
from nailgun.api.handlers.tasks import TaskHandler


class PluginCollectionHandler(JSONHandler):

    @content_json
    def GET(self):
        pass

    @content_json
    def POST(self):
        plugin_manager = PluginManager()
        task = plugin_manager.add_install_plugin_task(
            json.loads(web.data()))

        return TaskHandler.render(task)


class PluginHandler(JSONHandler):

    @content_json
    def GET(self, plugin_id):
        pass

    @content_json
    def DELETE(self):
        pass

    @content_json
    def PUT(self):
        pass
