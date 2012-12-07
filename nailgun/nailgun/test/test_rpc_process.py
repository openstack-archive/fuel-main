
import json
import string
from random import choice
from datetime import time

import eventlet
eventlet.monkey_patch()

import nailgun.rpc as rpc
from nailgun.test.base import BaseHandlers
from nailgun.rpc.processed import RPCProcess


class TestReceiver(object):
    @staticmethod
    def echo(value):
        """Simply returns whatever value is sent in."""
        return value


class TestRPCProcess(BaseHandlers):

    def setUp(self):
        super(TestRPCProcess, self).setUp()
        self.q_name = "".join([choice(string.ascii_lowercase) for _ in xrange(7)])
        self.process = RPCProcess(self.q_name, TestReceiver)
        self.process.start()
        self.conn = rpc.create_connection(True)

    def tearDown(self):
        if self.process.is_alive():
            self.process.terminate()
            self.process.join()
        else:
            raise Exception("RPC process terminated unexpectedly")
        self.conn.close()
        super(TestRPCProcess, self).tearDown()

    def test_echo_working(self):
        value = 42
        result = rpc.call(self.q_name, {"method": "echo", "args": {"value": value}})
        self.assertEqual(value, result)
