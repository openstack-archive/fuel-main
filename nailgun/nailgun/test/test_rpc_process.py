from datetime import time
import json

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
        self.process = RPCProcess('test', TestReceiver)
        self.process.start()
        self.conn = rpc.create_connection(True)

    def tearDown(self):
        if self.process.is_alive():
            self.process.terminate()
            self.process.join()
        else:
            raise Exception("RPC process terminated unexpectedly")
        super(TestRPCProcess, self).tearDown()

    def test_echo_working(self):
        value = 42
        result = rpc.call('test', {"method": "echo", "args": {"value": value}})
        self.assertEqual(value, result)
