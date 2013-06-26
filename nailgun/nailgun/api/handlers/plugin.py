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
