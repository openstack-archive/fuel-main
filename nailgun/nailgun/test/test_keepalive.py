# -*- coding: utf-8 -*-
import json
import time

from mock import patch

from nailgun.settings import settings

import nailgun
import nailgun.rpc as rpc
from nailgun.keepalive.watcher import KeepAliveThread
from nailgun.task.manager import DeploymentTaskManager
from nailgun.task.fake import FAKE_THREADS
from nailgun.task.errors import WrongNodeStatus
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.api.models import Cluster, Attributes, Task, Notification, Node
from nailgun.api.models import IPAddr, NetworkGroup, Network


class TestKeepalive(BaseHandlers):

    def setUp(self):
        super(TestKeepalive, self).setUp()
        self.watcher = KeepAliveThread(
            timeout=2,
            maxtime=1
        )
        self.watcher.start()

    def tearDown(self):
        self.watcher.join()

    def test_node_becomes_offline(self):
        node = self.create_default_node(status="discover",
                                        role="controller",
                                        name="Dead or alive")
        time.sleep(self.watcher.timeout + 1)
        self.db.refresh(node)
        self.assertEqual(node.status, "offline")
