# -*- coding: utf-8 -*-

import web
from settings import settings

render = web.template.render(settings.TEMPLATE_DIR)


class IndexHandler(object):
    def GET(self):
        return render.index()
