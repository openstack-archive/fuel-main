# -*- coding: utf-8 -*-

import time
import uuid

import eventlet
eventlet.monkey_patch()

import rpc
from rpc import threaded
from base import BaseHandlers
from api.models import Node, Task


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

        receiver.deploy_resp(
            task_uuid=task.uuid,
            nodes={
                str(node.id): {"status": "deploying"},
                str(node2.id): {"status": "error"}
            }
        )
        self.db.refresh(node)
        self.db.refresh(node2)
        self.db.refresh(task)
        if (node.status, node2.status) != ("deploying", "error"):
            raise Exception("Failed to update nodes")
        self.assertEqual(task.status, "error")
        print task.errors
        raise
