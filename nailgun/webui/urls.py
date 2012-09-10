# -*- coding: utf-8 -*-

import web

from webui.handlers import IndexHandler, StaticHandler

urls = (
    r"/static/(.*)", 'StaticHandler',
    r"/", 'IndexHandler',
)

webui_app = web.application(urls, locals())
