# -*- coding: utf-8 -*-

import json
import traceback
import web

from nailgun.logger import logger
from nailgun.api.models import Cluster
from nailgun.api.models import NetworkGroup
from nailgun.api.handlers.base import JSONHandler, content_json
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.task.helpers import update_task_status
from nailgun.task.manager import CheckNetworksTaskManager
from nailgun.task.manager import VerifyNetworksTaskManager


class NetworkConfigurationVerifyHandler(JSONHandler):
    @content_json
    def PUT(self, cluster_id):
        cluster = self.get_object_or_404(Cluster, cluster_id)
        data = json.loads(web.data())
        networks = data['networks']
        nets = NetworkGroup.validate_collection_update(json.dumps(networks))
        vlan_ids = NetworkGroup.generate_vlan_ids_list(networks)
        task_manager = VerifyNetworksTaskManager(cluster_id=cluster.id)
        task = task_manager.execute(data, vlan_ids)
        return TaskHandler.render(task)


class NetworkConfigurationHandler(JSONHandler):
    fields = ('id', 'cluster_id', 'name', 'cidr',
              'vlan_start', 'network_size', 'amount')

    @content_json
    def GET(self, cluster_id):
        cluster = self.get_object_or_404(Cluster, cluster_id)
        result = {}
        result['net_manager'] = cluster.net_manager
        result['networks'] = map(self.render, cluster.network_groups)

        return result

    @content_json
    def PUT(self, cluster_id):
        data = json.loads(web.data())
        cluster = self.get_object_or_404(Cluster, cluster_id)

        task_manager = CheckNetworksTaskManager(cluster_id=cluster.id)
        task = task_manager.execute(data)

        if 'net_manager' in data:
            setattr(cluster, 'net_manager', data['net_manager'])

        if 'networks' in data and task.status != 'error':
            new_nets = NetworkGroup.validate_collection_update(
                json.dumps(data['networks']))

            for ng in new_nets:
                ng_db = self.db.query(NetworkGroup).get(ng['id'])
                for key, value in ng.iteritems():
                    setattr(ng_db, key, value)
                try:
                    ng_db.create_networks()
                    ng_db.cluster.add_pending_changes('networks')
                except Exception as exc:
                    err = str(exc)
                    update_task_status(
                        task.uuid,
                        status="error",
                        progress=100,
                        msg=err
                    )
                    logger.error(traceback.format_exc())
                    break

        if task.status == 'error':
            self.db.rollback()
        else:
            self.db.commit()

        return TaskHandler.render(task)
