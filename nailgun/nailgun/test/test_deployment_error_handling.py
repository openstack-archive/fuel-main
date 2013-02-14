# -*- coding: utf-8 -*-
import json
import time
from functools import partial

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


def raise_(*args, **kwargs):
    raise kwargs.pop("ex")

alert = partial(raise_, ex=Exception("ALERT"))


class TestErrors(BaseHandlers):

    @patch('nailgun.task.task.rpc.cast')
    @patch('nailgun.task.task.DeploymentTask._provision', alert)
    def test_deployment_errors_update_cluster(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"pending_addition": True},
            ]
        )
        supertask = self.env.launch_deployment()
        self.env.wait_error(supertask, 60, "Failed to call cobbler: ALERT")
        self.db.refresh(supertask.cluster)
        self.assertEquals(supertask.cluster.status, 'error')
