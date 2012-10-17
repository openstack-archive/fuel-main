# -*- coding: utf-8 -*-

from datetime import time
import eventlet
eventlet.monkey_patch()

from unittest import TestCase

import nailgun.rpc as rpc


class TestTasks(TestCase):

    def setUp(self):
        self.conn = rpc.create_connection(True)
        self.receiver = TestReceiver()
        self.conn.create_consumer('test', self.receiver, False)
        self.conn.consume_in_thread()

    def tearDown(self):
        self.conn.close()

    def test_call_succeed(self):
        value = 42
        result = rpc.call('test', {"method": "echo", "args": {"value": value}})
        self.assertEqual(value, result)

    def test_reusing_connection(self):
        """Test that reusing a connection returns same one."""
        conn_context = rpc.create_connection(new=False)
        conn1 = conn_context.connection
        conn_context.close()
        conn_context = rpc.create_connection(new=False)
        conn2 = conn_context.connection
        conn_context.close()
        self.assertEqual(conn1, conn2)

    def test_topic_send_receive(self):
        """Test sending to a topic exchange/queue"""

        conn = rpc.create_connection()
        message = 'topic test message'

        self.received_message = None

        def _callback(message):
            self.received_message = message

        conn.declare_topic_consumer('a_topic', _callback)
        conn.topic_send('a_topic', message)
        conn.consume(limit=1)
        conn.close()

        self.assertEqual(self.received_message, message)

    def test_rpc_topic_send_receive(self):
        message = {"method": "hello", "args": {"value": 142}}
        conn = rpc.create_connection()

        def _callback(message):
            self.received_message = message

        conn.declare_topic_consumer('b_topic', _callback)

        rpc.cast('b_topic', message)

        conn.consume(limit=1)
        conn.close()

        self.assertEqual(self.received_message, message)

    def test_direct_send_receive(self):
        """Test sending to a direct exchange/queue"""
        conn = rpc.create_connection()
        message = 'direct test message'

        self.received_message = None

        def _callback(message):
            self.received_message = message

        conn.declare_direct_consumer('a_direct', _callback)
        conn.direct_send('a_direct', message)
        conn.consume(limit=1)
        conn.close()

        self.assertEqual(self.received_message, message)


class TestReceiver(object):
    """Simple Proxy class so the consumer has methods to call.

    Uses static methods because we aren't actually storing any state.

    """

    @staticmethod
    def echo(value):
        """Simply returns whatever value is sent in."""
        return value

    @staticmethod
    def multicall_three_nones(value):
        yield None
        yield None
        yield None

    @staticmethod
    def echo_three_times_yield(value):
        yield value
        yield value + 1
        yield value + 2

    @staticmethod
    def fail(value):
        """Raises an exception with the value sent in."""
        raise Exception(value)

    @staticmethod
    def block(value):
        time.sleep(2)
