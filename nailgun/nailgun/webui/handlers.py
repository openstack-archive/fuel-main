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

import mimetypes
import posixpath
import web

from nailgun.settings import settings

render = web.template.render(settings.TEMPLATE_DIR)


class IndexHandler(object):
    def GET(self):
        return render.index()


class StaticHandler(object):
    def GET(self, fl):
        fl_path = posixpath.join(settings.STATIC_DIR, fl)
        mimetype = mimetypes.guess_type(fl_path)[0]
        if mimetype:
            web.header("Content-Type", mimetype)
        try:
            f = open(fl_path, 'r')
            return f.read()
        except Exception:
            raise web.notfound()
