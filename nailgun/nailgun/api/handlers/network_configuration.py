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
Handlers dealing with network configurations
"""

import json
import traceback
import web

from nailgun.api.handlers.base import build_json_response
from nailgun.api.handlers.base import content_json
from nailgun.api.handlers.base import JSONHandler
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.api.models import Cluster
from nailgun.api.models import NetworkConfiguration
from nailgun.api.models import NetworkGroup
from nailgun.api.models import Task
from nailgun.api.serializers.network_configuration \
    import NetworkConfigurationSerializer
from nailgun.api.validators.network import NetworkConfigurationValidator
from nailgun.db import db
from nailgun.logger import logger
from nailgun.task.helpers import TaskHelper
from nailgun.task.manager import CheckNetworksTaskManager
from nailgun.task.manager import VerifyNetworksTaskManager


class NetworkConfigurationVerifyHandler(JSONHandler):
    """Network configuration verify handler
    """

    validator = NetworkConfigurationValidator

    @content_json
    def PUT(self, cluster_id):
        """:IMPORTANT: this method should be rewritten to be more RESTful

        :returns: JSONized Task object.
        :http: * 202 (network checking task failed)
               * 200 (network verification task started)
               * 404 (cluster not found in db)
        """
        cluster = self.get_object_or_404(Cluster, cluster_id)

        try:
            data = self.validator.validate_networks_update(web.data())
        except web.webapi.badrequest as exc:
            task = Task(name='check_networks', cluster=cluster)
            db().add(task)
            db().commit()
            TaskHelper.set_error(task.uuid, exc.data)
            logger.error(traceback.format_exc())

            json_task = build_json_response(TaskHandler.render(task))
            raise web.accepted(data=json_task)

        vlan_ids = [{
            'name': n['name'],
            'vlans': NetworkGroup.generate_vlan_ids_list(n)
        } for n in data['networks']]

        task_manager = VerifyNetworksTaskManager(cluster_id=cluster.id)
        task = task_manager.execute(data, vlan_ids)

        return TaskHandler.render(task)


class NetworkConfigurationHandler(JSONHandler):
    """Network configuration handler
    """

    validator = NetworkConfigurationValidator
    serializer = NetworkConfigurationSerializer

    @content_json
    def GET(self, cluster_id):
        """:returns: JSONized network configuration for cluster.
        :http: * 200 (OK)
               * 404 (cluster not found in db)
        """
        cluster = self.get_object_or_404(Cluster, cluster_id)
        return self.serializer.serialize_for_cluster(cluster)

    def PUT(self, cluster_id):
        """:returns: JSONized Task object.
        :http: * 202 (network checking task created)
               * 404 (cluster not found in db)
        """
        data = json.loads(web.data())
        cluster = self.get_object_or_404(Cluster, cluster_id)

        task_manager = CheckNetworksTaskManager(cluster_id=cluster.id)
        task = task_manager.execute(data)

        if task.status != 'error':
            try:
                if 'networks' in data:
                    self.validator.validate_networks_update(json.dumps(data))

                NetworkConfiguration.update(cluster, data)
            except web.webapi.badrequest as exc:
                TaskHelper.set_error(task.uuid, exc.data)
                logger.error(traceback.format_exc())
            except Exception as exc:
                TaskHelper.set_error(task.uuid, exc)
                logger.error(traceback.format_exc())

        data = build_json_response(TaskHandler.render(task))
        if task.status == 'error':
            db().rollback()
        else:
            db().commit()
        raise web.accepted(data=data)
