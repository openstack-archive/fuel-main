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

"""
Product registration handlers
"""

import base64
import json


from nailgun.api.handlers.base import content_json
from nailgun.api.handlers.base import JSONHandler
from nailgun.settings import settings


class FuelKeyHandler(JSONHandler):
    """ Fuel key handler"""

    @content_json
    def GET(self):
        """Returns Fuel Key data
        :returns: base64 of FUEL commit SHA, release version and Fuel UUID.
        :http: * 200 (OK)
        """
        key_data = {
            "sha": settings.COMMIT_SHA,
            "release": settings.PRODUCT_VERSION,
            "uuid": settings.FUEL_KEY
        }
        signature = base64.b64encode(json.dumps(key_data))
        key_data["signature"] = signature
        return {"key": base64.b64encode(json.dumps(key_data))}
