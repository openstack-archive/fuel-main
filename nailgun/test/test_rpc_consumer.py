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

    def test_node_status_update(self):
        node = self.create_default_node()
        rpc.cast('nailgun', {
            "method": "node_error",
            "args": {
                "node_id": node.id
            }
        })
        time.sleep(5)
        self.db.refresh(node)
        self.assertEqual(node.status, 'error')
