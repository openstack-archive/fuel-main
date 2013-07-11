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

import web
import traceback

from nailgun.db import db
from nailgun.api.models import Node
from nailgun.api.validators.node import NodeVolumesValidator
from nailgun.volumes.manager import VolumeManager
from nailgun.volumes.manager import DisksFormatConvertor
from nailgun.api.models import Node, NodeAttributes
from nailgun.api.handlers.base import JSONHandler, content_json
from nailgun.errors import errors
from nailgun.logger import logger


class NodeDisksHandler(JSONHandler):

    validator = NodeVolumesValidator

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        node_volumes = node.attributes.volumes
        return DisksFormatConvertor.format_disks_to_simple(node_volumes)

    @content_json
    def PUT(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        data = self.validator.validate(web.data())
        if node.cluster:
            node.cluster.add_pending_changes('disks', node_id=node.id)

        if not node.attributes:
            return web.notfound()

        node.attributes.volumes = \
            DisksFormatConvertor.format_disks_to_full(node, data)

        db().commit()

        return DisksFormatConvertor.format_disks_to_simple(
            node.attributes.volumes)


class NodeDefaultsDisksHandler(JSONHandler):

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        if not node.attributes:
            return web.notfound()

        node_attrs = DisksFormatConvertor.format_disks_to_simple(
            VolumeManager.get_defaults_info(node))

        return filter(lambda attr: attr['type'] == 'disk', node_attrs)


class NodeVolumesInformationHandler(JSONHandler):

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)

        volumes_info = []
        try:
            volumes_info = DisksFormatConvertor.get_volumes_info(node)
        except errors.CannotFindVolumesInfoForRole as exc:
            logger.error(traceback.format_exc())
            raise web.notfound(
                message='Cannot calculate volumes info. '
                'Please, add node to a cluster.')

        return volumes_info
