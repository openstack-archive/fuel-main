# -*- coding: utf-8 -*-

import web

from nailgun.webui.handlers import IndexHandler, StaticHandler

urls = (
    r"/static/(.*)", 'StaticHandler',
    r"/", 'IndexHandler',
)

app = web.application(urls, locals())
