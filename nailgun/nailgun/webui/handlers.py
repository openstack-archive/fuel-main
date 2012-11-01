# -*- coding: utf-8 -*-

import web
import mimetypes
import posixpath

from nailgun.settings import settings
from nailgun.logger import logger

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
        except:
            raise web.notfound()
