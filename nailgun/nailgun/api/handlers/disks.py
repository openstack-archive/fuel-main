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
Handlers dealing with disks
"""

import traceback
import web

from nailgun.api.handlers.base import content_json
from nailgun.api.handlers.base import JSONHandler
from nailgun.api.models import Node
from nailgun.api.models import NodeAttributes
from nailgun.api.validators.node import NodeDisksValidator
from nailgun.db import db
from nailgun.errors import errors
from nailgun.logger import logger
from nailgun.volumes.manager import DisksFormatConvertor


class NodeDisksHandler(JSONHandler):
    """Node disks handler
    """

    validator = NodeDisksValidator

    @content_json
    def GET(self, node_id):
        """:returns: JSONized node disks.
        :http: * 200 (OK)
               * 404 (node not found in db)
        """
        node = self.get_object_or_404(Node, node_id)
        node_volumes = node.attributes.volumes
        return DisksFormatConvertor.format_disks_to_simple(node_volumes)

    @content_json
    def PUT(self, node_id):
        """:returns: JSONized node disks.
        :http: * 200 (OK)
               * 400 (invalid disks data specified)
               * 404 (node not found in db)
        """
        node = self.get_object_or_404(Node, node_id)
        data = self.checked_data()

        if node.cluster:
            node.cluster.add_pending_changes('disks', node_id=node.id)

        volumes_data = DisksFormatConvertor.format_disks_to_full(node, data)
        # For some reasons if we update node attributes like
        #   node.attributes.volumes = volumes_data
        # after
        #   db().commit()
        # it resets to previous state
        db().query(NodeAttributes).filter_by(node_id=node_id).update(
            {'volumes': volumes_data})
        db().commit()

        return DisksFormatConvertor.format_disks_to_simple(
            node.attributes.volumes)


class NodeDefaultsDisksHandler(JSONHandler):
    """Node default disks handler
    """

    @content_json
    def GET(self, node_id):
        """:returns: JSONized node disks.
        :http: * 200 (OK)
               * 404 (node or its attributes not found in db)
        """
        node = self.get_object_or_404(Node, node_id)
        if not node.attributes:
            return web.notfound()

        volumes = DisksFormatConvertor.format_disks_to_simple(
            node.volume_manager.gen_volumes_info())

        return volumes


class NodeVolumesInformationHandler(JSONHandler):
    """Node volumes information handler
    """

    @content_json
    def GET(self, node_id):
        """:returns: JSONized volumes info for node.
        :http: * 200 (OK)
               * 404 (node not found in db)
        """
        node = self.get_object_or_404(Node, node_id)

        volumes_info = []
        try:
            volumes_info = DisksFormatConvertor.get_volumes_info(node)
        except errors.CannotFindVolumesInfoForRole:
            logger.error(traceback.format_exc())
            raise web.notfound(
                message='Cannot calculate volumes info. '
                'Please, add node to a cluster.')

        return volumes_info
