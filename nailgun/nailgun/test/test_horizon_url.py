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
from nailgun.test.base import fake_tasks
from nailgun.api.models import Cluster, Attributes, Task, Notification, Node
from nailgun.api.models import IPAddr, NetworkGroup, Network


class TestHorizonURL(BaseHandlers):

    def tearDown(self):
        self._wait_for_threads()

    @fake_tasks()
    def test_horizon_url_ha_mode(self):
        self.env.create(
            cluster_kwargs={"mode": "ha"},
            nodes_kwargs=[
                {"pending_addition": True},
            ]
        )

        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask, 60)

        network = self.db.query(Network).join(NetworkGroup).\
            filter(NetworkGroup.cluster_id == self.env.clusters[0].id).\
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
            self.env.clusters[0].name,
            lost_ips[0].ip_addr
        ))
