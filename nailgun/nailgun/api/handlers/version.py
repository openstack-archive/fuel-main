# -*- coding: utf-8 -*-

import os
import web
import json

from nailgun.settings import settings
from nailgun.api.handlers.base import JSONHandler, content_json


class VersionHandler(JSONHandler):

    @content_json
    def GET(self):
        return {
            "sha": str(settings.COMMIT_SHA),
            "release": str(settings.PRODUCT_VERSION),
            "fuel_sha": str(settings.FUEL_COMMIT_SHA)
        }
