# -*- coding: utf-8 -*-

import web


class IndexHandler(object):
    def GET(self):
        render = web.template.render('static/')
        return render.index()
