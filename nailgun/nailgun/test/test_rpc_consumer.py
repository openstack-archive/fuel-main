# -*- coding: utf-8 -*-

import time
import uuid

import eventlet
eventlet.monkey_patch()

import nailgun.rpc as rpc
from nailgun.rpc import threaded
from nailgun.test.base import BaseHandlers
from nailgun.api.models import Node, Task


class TestConsumer(BaseHandlers):

    def test_node_deploy_resp(self):
        node = self.create_default_node()
        node2 = self.create_default_node()
        receiver = threaded.NailgunReceiver()

        task = Task(
            uuid=str(uuid.uuid4()),
            name="Test task"
        )
        self.db.add(task)
        self.db.commit()

        kwargs = {'task_uuid': task.uuid,
                  'nodes': [{'uid': node.fqdn, 'status': 'deploying'},
                            {'uid': node2.fqdn, 'status': 'error'}]}
        receiver.deploy_resp(**kwargs)
        self.db.refresh(node)
        self.db.refresh(node2)
        self.db.refresh(task)
        self.assertEqual((node.status, node2.status), ("deploying", "error"))
        self.assertEqual(task.status, "error")
