# -*- coding: utf-8 -*-

import json
import traceback
import web

from nailgun.logger import logger
from nailgun.api.validators import NetworkConfigurationValidator
from nailgun.api.models import Cluster
from nailgun.api.models import NetworkGroup
from nailgun.api.models import NetworkConfiguration
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.task.helpers import update_task_status
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
        data = self.validator.validate_networks_update(web.data())
        vlan_ids = NetworkGroup.generate_vlan_ids_list(data['networks'])
        task_manager = VerifyNetworksTaskManager(cluster_id=cluster.id)
        task = task_manager.execute(data, vlan_ids)

        return TaskHandler.render(task)


class NetworkConfigurationHandler(JSONHandler):
    fields = ('id', 'cluster_id', 'name', 'cidr',
              'vlan_start', 'network_size', 'amount')

    validator = NetworkConfigurationValidator

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
            if 'networks' in data:
                network_configuration = self.validator.\
                    validate_networks_update(json.dumps(data))
            try:
                NetworkConfiguration.update(cluster, data)
            except Exception as exc:
                err = str(exc)
                update_task_status(
                    task.uuid,
                    status="error",
                    progress=100,
                    msg=err
                )
                logger.error(traceback.format_exc())

        data = build_json_response(TaskHandler.render(task))
        if task.status == 'error':
            self.db.rollback()
            raise web.badrequest(message=data)

        self.db.commit()
        raise web.accepted(data=data)
