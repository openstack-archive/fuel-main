# -*- coding: utf-8 -*-

import json
import traceback
import web

from nailgun.logger import logger
from nailgun.network.manager import NetworkManager
from nailgun.api.validators import NetworkGroupValidator
from nailgun.api.models import Cluster
from nailgun.api.models import NetworkGroup
from nailgun.api.handlers.tasks import TaskHandler
from nailgun.task.helpers import update_task_status
from nailgun.task.manager import CheckNetworksTaskManager
from nailgun.task.manager import VerifyNetworksTaskManager
from nailgun.api.handlers.base \
    import JSONHandler, content_json, build_json_response


class NetworkConfigurationVerifyHandler(JSONHandler):

    validator = NetworkGroupValidator

    @content_json
    def PUT(self, cluster_id):
        cluster = self.get_object_or_404(Cluster, cluster_id)
        data = json.loads(web.data())
        networks = data['networks']
        self.validator.validate_collection_update(json.dumps(networks))
        vlan_ids = NetworkGroup.generate_vlan_ids_list(networks)
        task_manager = VerifyNetworksTaskManager(cluster_id=cluster.id)
        task = task_manager.execute(data, vlan_ids)
        return TaskHandler.render(task)


class NetworkConfigurationHandler(JSONHandler):
    fields = ('id', 'cluster_id', 'name', 'cidr',
              'vlan_start', 'network_size', 'amount')

    validator = NetworkGroupValidator

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

        network_manager = NetworkManager()
        task_manager = CheckNetworksTaskManager(cluster_id=cluster.id)
        task = task_manager.execute(data)

        if 'net_manager' in data:
            setattr(cluster, 'net_manager', data['net_manager'])

        if 'networks' in data and task.status != 'error':
            new_nets = self.validator.validate_collection_update(
                json.dumps(data['networks']))

            for ng in new_nets:
                ng_db = self.db.query(NetworkGroup).get(ng['id'])
                for key, value in ng.iteritems():
                    setattr(ng_db, key, value)
                try:
                    network_manager.create_networks(ng_db)
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

        data = build_json_response(TaskHandler.render(task))
        if task.status == 'error':
            self.db.rollback()
            raise web.badrequest(message=data)

        self.db.commit()
        raise web.accepted(data=data)
