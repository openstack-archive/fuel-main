# -*- coding: utf-8 -*-

import json
import traceback
import web

from nailgun.logger import logger
from nailgun.api.validators import NetworkConfigurationValidator
from nailgun.api.models import Cluster
from nailgun.api.models import NetworkGroup
from nailgun.api.models import NetworkConfiguration
from nailgun.api.models import Task
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.task.helpers import TaskHelper
from nailgun.network.manager import NetworkManager
from nailgun.task.manager import CheckNetworksTaskManager
from nailgun.task.manager import VerifyNetworksTaskManager
from nailgun.api.handlers.base \
    import JSONHandler, content_json, build_json_response


class NetworkConfigurationVerifyHandler(JSONHandler):

    validator = NetworkConfigurationValidator

    @content_json
    def PUT(self, cluster_id):
        cluster = self.get_object_or_404(Cluster, cluster_id)

        try:
            data = self.validator.validate_networks_update(web.data())
        except web.webapi.badrequest as exc:
            task = Task(name='check_networks', cluster=cluster)
            self.db.add(task)
            self.db.commit()
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
    fields = ('id', 'cluster_id', 'name', 'cidr', 'netmask',
              'gateway', 'vlan_start', 'network_size', 'amount')

    validator = NetworkConfigurationValidator

    @classmethod
    def render(cls, instance, fields=None):
        json_data = JSONHandler.render(instance, fields=cls.fields)
        json_data["ip_ranges"] = [
            [ir.first, ir.last] for ir in instance.ip_ranges
        ]
        json_data.setdefault("netmask", "")
        json_data.setdefault("gateway", "")
        return json_data

    @content_json
    def GET(self, cluster_id):
        cluster = self.get_object_or_404(Cluster, cluster_id)
        result = {}
        result['net_manager'] = cluster.net_manager
        result['networks'] = map(self.render, cluster.network_groups)
        return result

    def PUT(self, cluster_id):
        data = json.loads(web.data())
        cluster = self.get_object_or_404(Cluster, cluster_id)

        task_manager = CheckNetworksTaskManager(cluster_id=cluster.id)
        task = task_manager.execute(data)

        if task.status != 'error':
            try:
                if 'networks' in data:
                    network_configuration = self.validator.\
                        validate_networks_update(json.dumps(data))

                NetworkConfiguration.update(cluster, data)
            except web.webapi.badrequest as exc:
                TaskHelper.set_error(task.uuid, exc.data)
                logger.error(traceback.format_exc())
            except Exception as exc:
                TaskHelper.set_error(task.uuid, exc)
                logger.error(traceback.format_exc())

        data = build_json_response(TaskHandler.render(task))
        if task.status == 'error':
            self.db.rollback()
        else:
            self.db.commit()
        raise web.accepted(data=data)
