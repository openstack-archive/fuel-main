# -*- coding: utf-8 -*-

import web

from webui.handlers import IndexHandler

urls = (
	r"", 'IndexHandler',
)

webui_app = web.application(urls, locals())