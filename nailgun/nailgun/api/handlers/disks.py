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

from nailgun.db import db
from nailgun.api.models import Node
from nailgun.api.validators.node import NodeVolumesValidator
from nailgun.volumes.manager import VolumeManager
from nailgun.api.models import Node, NodeAttributes
from nailgun.api.handlers.base import JSONHandler, content_json


class NodeDisksHandler(JSONHandler):
    fields = ('node_id', 'volumes')

    validator = NodeVolumesValidator

    @classmethod
    def render(cls, instance, fields=None):
        return JSONHandler.render(instance, fields=cls.fields)['volumes']

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        node_attrs = node.attributes
        if not node_attrs:
            return web.notfound()

        return self.render(node_attrs)

    @content_json
    def PUT(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        data = self.validator.validate(web.data())
        if node.cluster:
            node.cluster.add_pending_changes('disks', node_id=node.id)

        if not node.attributes:
            return web.notfound()

        node.attributes.volumes = data
        db().commit()
        return self.render(node.attributes)


class NodeDefaultsDisksHandler(JSONHandler):

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        if not node.attributes:
            return web.notfound()

        node_attrs = NodeDisksHandler.render(
            NodeAttributes(
                node_id=node.id,
                volumes=node.volume_manager.gen_volumes_info()))

        return filter(lambda attr: attr['type'] == 'disk', node_attrs)


class NodeVolumesInformationHandler(JSONHandler):

    @content_json
    def GET(self, node_id):
        node = self.get_object_or_404(Node, node_id)
        if not node.attributes:
            return web.notfound()

        node_attrs = NodeDisksHandler.render(
            NodeAttributes(
                node_id=node.id,
                volumes=node.volume_manager.gen_volumes_info()))

        return filter(lambda attr: attr['type'] == 'vg', node_attrs)
