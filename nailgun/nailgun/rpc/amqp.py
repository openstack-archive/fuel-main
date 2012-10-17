"""
Shared code between AMQP based nailgun.rpc implementations.
"""
import inspect
import sys
import traceback
import uuid
import logging

from eventlet import greenpool
from eventlet import pools


LOG = logging.getLogger(__name__)


class Pool(pools.Pool):
    """Class that implements a Pool of Connections."""
    def __init__(self, *args, **kwargs):
        self.connection_cls = kwargs.pop("connection_cls", None)
        kwargs.setdefault("max_size", 30)
        kwargs.setdefault("order_as_stack", True)
        super(Pool, self).__init__(*args, **kwargs)

    # TODO(comstud): Timeout connections not used in a while
    def create(self):
        LOG.debug('Pool creating new connection')
        return self.connection_cls()

    def empty(self):
        while self.free_items:
            self.get().close()


class ConnectionContext(object):
    """The class that is actually returned to the caller of
    create_connection().  This is a essentially a wrapper around
    Connection that supports 'with' and can return a new Connection or
    one from a pool.  It will also catch when an instance of this class
    is to be deleted so that we can return Connections to the pool on
    exceptions and so forth without making the caller be responsible for
    catching all exceptions and making sure to return a connection to
    the pool.
    """

    def __init__(self, connection_pool, pooled=True, server_params=None):
        """Create a new connection, or get one from the pool"""
        self.connection = None
        self.connection_pool = connection_pool
        if pooled:
            self.connection = connection_pool.get()
        else:
            self.connection = connection_pool.connection_cls(
                server_params=server_params)
        self.pooled = pooled

    def __enter__(self):
        """When with ConnectionContext() is used, return self"""
        return self

    def _done(self):
        """If the connection came from a pool, clean it up and put it back.
        If it did not come from a pool, close it.
        """
        if self.connection:
            if self.pooled:
                # Reset the connection so it's ready for the next caller
                # to grab from the pool
                self.connection.reset()
                self.connection_pool.put(self.connection)
            else:
                try:
                    self.connection.close()
                except Exception:
                    pass
            self.connection = None

    def __exit__(self, exc_type, exc_value, tb):
        """End of 'with' statement.  We're done here."""
        self._done()

    def __del__(self):
        """Caller is done with this connection.  Make sure we cleaned up."""
        self._done()

    def close(self):
        """Caller is done with this connection."""
        self._done()

    def create_consumer(self, topic, proxy, fanout=False):
        self.connection.create_consumer(topic, proxy, fanout)

    def consume_in_thread(self):
        return self.connection.consume_in_thread()

    def __getattr__(self, key):
        """Proxy all other calls to the Connection instance"""
        if self.connection:
            return getattr(self.connection, key)
        else:
            #raise exception.InvalidRPCConnectionReuse()
            raise Exception("InvalidRPCConnectionReuse")


def msg_reply(msg_id, connection_pool, reply=None, failure=None, ending=False):
    """Sends a reply or an error on the channel signified by msg_id.

    Failure should be a sys.exc_info() tuple.

    """
    with ConnectionContext(connection_pool) as conn:
        if failure:
            message = str(failure[1])
            tb = traceback.format_exception(*failure)
            LOG.error("Returning exception %s to caller", message)
            LOG.error(tb)
            failure = (failure[0].__name__, str(failure[1]), tb)

        try:
            msg = {'result': reply, 'failure': failure}
        except TypeError:
            msg = {
                'result': dict((k, repr(v)) for k, v in reply.__dict__.
                iteritems()),
                'failure': failure}
        if ending:
            msg['ending'] = True
        conn.direct_send(msg_id, msg)


class ProxyCallback(object):
    """Calls methods on a proxy object based on method and args."""

    def __init__(self, proxy, connection_pool):
        self.proxy = proxy
        self.pool = greenpool.GreenPool(1024)  # 1024 - thread pool size
        self.connection_pool = connection_pool

    def __call__(self, message_data):
        """Consumer callback to call a method on a proxy object.

        Parses the message for validity and fires off a thread to call the
        proxy object method.

        Message data should be a dictionary with two keys:
            method: string representing the method to call
            args: dictionary of arg: value

        Example: {'method': 'echo', 'args': {'value': 42}}

        """
        # It is important to clear the context here, because at this point
        # the previous context is stored in local.store.context
        #if hasattr(local.store, 'context'):
            #del local.store.context
        LOG.debug('received %s' % message_data)
        #ctxt = unpack_context(message_data)
        method = message_data.get('method')
        msg_id = message_data.pop('msg_id', None)
        args = message_data.get('args', {})
        if not method:
            LOG.warn('no method for message: %s' % message_data)
            reply = 'No method for message: %s' % message_data
            msg_reply(
                msg_id, self.connection_pool, reply=reply,
                failure=None, ending=False)
            return
        self.pool.spawn_n(self._process_data, msg_id, method, args)

    def _process_data(self, msg_id, method, args):
        """Thread that magically looks for a method on the proxy
        object and calls it.
        """
        try:
            node_func = getattr(self.proxy, str(method))
            node_args = dict((str(k), v) for k, v in args.iteritems())
            # NOTE(vish): magic is fun!
            rval = node_func(**node_args)
            # Check if the result was a generator
            if inspect.isgenerator(rval):
                for x in rval:
                    msg_reply(
                        msg_id, self.connection_pool, reply=x,
                        failure=None, ending=False)
            else:
                msg_reply(msg_id, self.connection_pool, reply=rval)
            # This final None tells multicall that it is done.
            msg_reply(msg_id, self.connection_pool, ending=True)
        except Exception as e:
            LOG.exception('Exception during message handling')
            msg_reply(
                msg_id, self.connection_pool, reply=None,
                failure=sys.exc_info(), ending=False)
        return


class MulticallWaiter(object):
    def __init__(self, connection, timeout):
        self._connection = connection
        # TODO resp timeout
        self._iterator = connection.iterconsume(timeout=timeout or 20)
        self._result = None
        self._done = False
        self._got_ending = False

    def done(self):
        if self._done:
            return
        self._done = True
        self._iterator.close()
        self._iterator = None
        self._connection.close()

    def __call__(self, data):
        """The consume() callback will call this.  Store the result."""
        if data['failure']:
            # TODO show remote exception
            #self._result = rpc_common.RemoteError(*data['failure'])
            self._result = data['failure']
        elif data.get('ending', False):
            self._got_ending = True
        else:
            self._result = data['result']

    def __iter__(self):
        """Return a result until we get a 'None' response from consumer"""
        if self._done:
            raise StopIteration
        while True:
            self._iterator.next()
            if self._got_ending:
                self.done()
                raise StopIteration
            result = self._result
            if isinstance(result, Exception):
                self.done()
                raise result
            yield result


def multicall(topic, msg, timeout, connection_pool):
    """Make a call that returns multiple times."""
    # Can't use 'with' for multicall, as it returns an iterator
    # that will continue to use the connection.  When it's done,
    # connection.close() will get called which will put it back into
    # the pool
    LOG.debug('Making asynchronous call on %s ...', topic)
    msg_id = uuid.uuid4().hex
    msg.update({'msg_id': msg_id})
    LOG.debug('MSG_ID is %s' % (msg_id))

    conn = ConnectionContext(connection_pool)
    wait_msg = MulticallWaiter(conn, timeout)
    conn.declare_direct_consumer(msg_id, wait_msg)
    conn.topic_send(topic, msg)
    return wait_msg


def call(topic, msg, timeout, connection_pool):
    """Sends a message on a topic and wait for a response."""
    rv = multicall(topic, msg, timeout, connection_pool)
    # NOTE(vish): return the last result from the multicall
    rv = list(rv)
    if not rv:
        return
    return rv[-1]


def create_connection(new, connection_pool):
    """Create a connection"""
    return ConnectionContext(connection_pool, pooled=not new)


def cast(topic, msg, connection_pool):
    """Sends a message on a topic without waiting for a response."""
    LOG.debug('Making asynchronous cast on %s...', topic)
    with ConnectionContext(connection_pool) as conn:
        conn.topic_send(topic, msg)


def cleanup(connection_pool):
    connection_pool.empty()
