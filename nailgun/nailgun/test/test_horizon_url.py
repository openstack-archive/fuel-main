# -*- coding: utf-8 -*-
import json
import time

from mock import patch

from nailgun.settings import settings

import nailgun
import nailgun.rpc as rpc
from nailgun.task.manager import DeploymentTaskManager
from nailgun.task.fake import FAKE_THREADS
from nailgun.task.errors import WrongNodeStatus
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster, Attributes, Task, Notification, Node
from nailgun.api.models import IPAddr, NetworkGroup, Network


class TestHorizonURL(BaseHandlers):

    def tearDown(self):
        # wait for fake task thread termination
        import threading
        for thread in threading.enumerate():
            if thread is not threading.currentThread():
                if hasattr(thread, "rude_join"):
                    timer = time.time()
                    timeout = 25
                    thread.rude_join(timeout)
                    if time.time() - timer > timeout:
                        raise Exception(
                            '{0} seconds is not enough'
                            ' - possible hanging'.format(
                                timeout
                            )
                        )

    @patch('nailgun.task.task.rpc.cast', nailgun.task.task.fake_cast)
    @patch('nailgun.task.task.settings.FAKE_TASKS', True)
    @patch('nailgun.task.fake.settings.FAKE_TASKS_TICK_COUNT', 80)
    @patch('nailgun.task.fake.settings.FAKE_TASKS_TICK_INTERVAL', 1)
    def test_horizon_url_ha_mode(self):
        cluster = self.create_cluster_api(mode="ha")
        node = self.create_default_node(cluster_id=cluster['id'],
                                        status="discover",
                                        role="controller",
                                        pending_addition=True)
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster['id']}),
            headers=self.default_headers
        )
        response = json.loads(resp.body)
        supertask_uuid = response['uuid']
        supertask = self.db.query(Task).filter_by(
            uuid=supertask_uuid
        ).first()

        timer = time.time()
        timeout = 60
        while supertask.status == 'running':
            self.db.refresh(supertask)
            if time.time() - timer > timeout:
                raise Exception("Deployment seems to be hanged")
            time.sleep(1)
        self.db.refresh(node)
        self.assertEquals(supertask.status, 'ready')
        self.assertEquals(supertask.progress, 100)

        network = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == cluster["id"]).\
            filter_by(name="public").first()
        lost_ips = self.db.query(IPAddr).filter_by(
            network=network.id,
            node=None
        ).all()
        self.assertEquals(len(lost_ips), 1)

        self.assertEquals(supertask.message, (
            u"Deployment of environment '{0}' is done. "
            "Access WebUI of OpenStack at http://{1}/"
        ).format(
            cluster['name'],
            lost_ips[0].ip_addr
        ))
