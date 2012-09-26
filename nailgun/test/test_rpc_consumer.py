# -*- coding: utf-8 -*-

import time
import eventlet
eventlet.monkey_patch()

import rpc
from rpc import threaded
from base import BaseHandlers
from api.models import Node


class TestConsumer(BaseHandlers):

    def setUp(self):
        super(TestConsumer, self).setUp()
        self.conn = rpc.create_connection(True)
        self.rpc_thread = threaded.RPCThread()
        self.rpc_thread.start()

    def tearDown(self):
        super(TestConsumer, self).tearDown()
        self.conn.close()

    def test_node_deploy_resp(self):
        node = self.create_default_node()
        node2 = self.create_default_node()
        rpc.cast('nailgun', {
            "method": "deploy_resp",
            "args": {
                "nodes": {
                    str(node.id): {"status": "deploying"},
                    str(node2.id): {"status": "error"}
                }
            }
        })
        timer = time.time()
        while True:
            self.db.refresh(node)
            self.db.refresh(node2)
            if (node.status, node2.status) == ("deploying", "error"):
                break
            if time.time() - timer > 5:
                raise Exception("Resp timeout expired")
