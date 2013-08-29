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

from nailgun.api.models import Attributes
from nailgun.api.models import Release
from nailgun.api.validators.base import BasicValidator
from nailgun.db import db
from nailgun.errors import errors
from nailgun.settings import settings


class ReleaseValidator(BasicValidator):

    @classmethod
    def validate(cls, data):
        d = cls.validate_json(data)
        if "name" not in d:
            raise errors.InvalidData(
                "No release name specified",
                log_message=True
            )
        if "version" not in d:
            raise errors.InvalidData(
                "No release version specified",
                log_message=True
            )
        if db().query(Release).filter_by(
            name=d["name"],
            version=d["version"]
        ).first():
            raise errors.AlreadyExists(
                "Release with the same name and version "
                "already exists",
                log_message=True
            )
        if "networks_metadata" in d:
            for network in d["networks_metadata"]:
                if not "name" in network or not "access" in network:
                    raise errors.InvalidData(
                        "Invalid network data: %s" % str(network),
                        log_message=True
                    )
                if network["access"] not in settings.NETWORK_POOLS:
                    raise errors.InvalidData(
                        "Invalid access mode for network",
                        log_message=True
                    )
        else:
            d["networks_metadata"] = []
        if "attributes_metadata" not in d:
            d["attributes_metadata"] = {}
        else:
            try:
                Attributes.validate_fixture(d["attributes_metadata"])
            except Exception:
                raise errors.InvalidData(
                    "Invalid logical structure of attributes metadata",
                    log_message=True
                )
        return d
