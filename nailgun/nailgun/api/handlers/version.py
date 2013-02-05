# -*- coding: utf-8 -*-

import os
import web
import json

from nailgun.settings import settings
from nailgun.api.handlers.base import JSONHandler


class VersionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        return json.dumps({
            "sha": str(settings.COMMIT_SHA or "Unknown"),
            "version": str(settings.PRODUCT_VERSION or "Unknown")
        })
