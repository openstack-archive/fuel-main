# -*- coding: utf-8 -*-

import time
import eventlet
eventlet.monkey_patch()

import rpc
from rpc import threaded
from base import BaseHandlers
from api.models import Node


class TestConsumer(BaseHandlers):

    def test_node_deploy_resp(self):
        node = self.create_default_node()
        node2 = self.create_default_node()
        receiver = threaded.NailgunReceiver()

        receiver.deploy_resp(
            nodes={
                str(node.id): {"status": "deploying"},
                str(node2.id): {"status": "error"}
            }
        )
        self.db.refresh(node)
        self.db.refresh(node2)
        if (node.status, node2.status) != ("deploying", "error"):
            raise Exception("Failed to update nodes")
