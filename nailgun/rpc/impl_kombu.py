import logging
import itertools
import socket
import sys
import time
import uuid

import greenlet
import eventlet
import kombu
import kombu.entity
import kombu.messaging
import kombu.connection

from rpc import amqp as rpc_amqp

LOG = logging.getLogger(__name__)


class ConsumerBase(object):
    """Consumer base class."""

    def __init__(self, channel, callback, tag, **kwargs):
        """Declare a queue on an amqp channel.

        'channel' is the amqp channel to use
        'callback' is the callback to call when messages are received
        'tag' is a unique ID for the consumer on the channel

        queue name, exchange name, and other kombu options are
        passed in here as a dictionary.
        """
        self.callback = callback
        self.tag = str(tag)
        self.kwargs = kwargs
        self.queue = None
        self.reconnect(channel)

    def reconnect(self, channel):
        """Re-declare the queue after a rabbit reconnect"""
        self.channel = channel
        self.kwargs['channel'] = channel
        self.queue = kombu.entity.Queue(**self.kwargs)
        self.queue.declare()

    def consume(self, *args, **kwargs):
        """Actually declare the consumer on the amqp channel.  This will
        start the flow of messages from the queue.  Using the
        Connection.iterconsume() iterator will process the messages,
        calling the appropriate callback.

        If a callback is specified in kwargs, use that.  Otherwise,
        use the callback passed during __init__()

        If kwargs['nowait'] is True, then this call will block until
        a message is read.

        Messages will automatically be acked if the callback doesn't
        raise an exception
        """

        options = {'consumer_tag': self.tag}
        options['nowait'] = kwargs.get('nowait', False)
        callback = kwargs.get('callback', self.callback)
        if not callback:
            raise ValueError("No callback defined")

        def _callback(raw_message):
            message = self.channel.message_to_python(raw_message)
            try:
                callback(message.payload)
                message.ack()
            except Exception:
                LOG.exception("Failed to process message... skipping it.")

        self.queue.consume(*args, callback=_callback, **options)

    def cancel(self):
        """Cancel the consuming from the queue, if it has started"""
        try:
            self.queue.cancel(self.tag)
        except KeyError, e:
            # NOTE(comstud): Kludge to get around a amqplib bug
            if str(e) != "u'%s'" % self.tag:
                raise
        self.queue = None


class DirectConsumer(ConsumerBase):
    """Queue/consumer class for 'direct'"""

    def __init__(self, channel, msg_id, callback, tag, **kwargs):
        """Init a 'direct' queue.

        'channel' is the amqp channel to use
        'msg_id' is the msg_id to listen on
        'callback' is the callback to call when messages are received
        'tag' is a unique ID for the consumer on the channel

        Other kombu options may be passed
        """
        # Default options
        options = {'durable': False,
                'auto_delete': True,
                'exclusive': True}
        options.update(kwargs)
        exchange = kombu.entity.Exchange(
                name=msg_id,
                type='direct',
                durable=options['durable'],
                auto_delete=options['auto_delete'])
        super(DirectConsumer, self).__init__(
                channel,
                callback,
                tag,
                name=msg_id,
                exchange=exchange,
                routing_key=msg_id,
                **options)


class TopicConsumer(ConsumerBase):
    """Consumer class for 'topic'"""

    def __init__(self, channel, topic, callback, tag, **kwargs):
        """Init a 'topic' queue.

        'channel' is the amqp channel to use
        'topic' is the topic to listen on
        'callback' is the callback to call when messages are received
        'tag' is a unique ID for the consumer on the channel

        Other kombu options may be passed
        """
        # Default options
        options = {'durable': False,
                'auto_delete': False,
                'exclusive': False}
        options.update(kwargs)
        exchange = kombu.entity.Exchange(
                name='nailgun',
                type='topic',
                durable=options['durable'],
                auto_delete=options['auto_delete'])
        super(TopicConsumer, self).__init__(
                channel,
                callback,
                tag,
                name=topic,
                exchange=exchange,
                routing_key=topic,
                **options)


class Publisher(object):
    """Base Publisher class"""

    def __init__(self, channel, exchange_name, routing_key, **kwargs):
        """Init the Publisher class with the exchange_name, routing_key,
        and other options
        """
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.kwargs = kwargs
        self.reconnect(channel)

    def reconnect(self, channel):
        """Re-establish the Producer after a rabbit reconnection"""
        self.exchange = kombu.entity.Exchange(name=self.exchange_name,
                **self.kwargs)
        self.producer = kombu.messaging.Producer(exchange=self.exchange,
                channel=channel, routing_key=self.routing_key)

    def send(self, msg):
        """Send a message"""
        self.producer.publish(msg)


class DirectPublisher(Publisher):
    """Publisher class for 'direct'"""
    def __init__(self, channel, msg_id, **kwargs):
        """init a 'direct' publisher.

        Kombu options may be passed as keyword args to override defaults
        """

        options = {'durable': False,
                'auto_delete': True,
                'exclusive': True}
        options.update(kwargs)
        super(DirectPublisher, self).__init__(channel,
                msg_id,
                msg_id,
                type='direct',
                **options)


class TopicPublisher(Publisher):
    """Publisher class for 'topic'"""
    def __init__(self, channel, topic, **kwargs):
        """init a 'topic' publisher.

        Kombu options may be passed as keyword args to override defaults
        """

        options = {'durable': False,
                'auto_delete': False,
                'exclusive': False}
        options.update(kwargs)
        super(TopicPublisher, self).__init__(channel,
                'nailgun',
                topic,
                type='topic',
                **options)


class Connection(object):
    """Connection object."""

    def __init__(self, server_params=None):
        self.consumers = []
        self.consumer_thread = None
        # Try forever
        self.max_retries = None
        self.interval_start = 1
        self.interval_stepping = 2
        # max retry-interval = 30 seconds
        self.interval_max = 30
        self.memory_transport = False

        if server_params is None:
            server_params = {}

        # Keys to translate from server_params to kombu params
        server_params_to_kombu_params = {'username': 'userid'}

        params = {}
        for sp_key, value in server_params.iteritems():
            p_key = server_params_to_kombu_params.get(sp_key, sp_key)
            params[p_key] = value

        # TODO
        # (mihgen) Will do it right when config file of new Nailgun available
        params.setdefault('hostname', 'localhost')
        params.setdefault('port', 5672)
        params.setdefault('userid', 'guest')
        params.setdefault('password', 'guest')
        params.setdefault('virtual_host', '/')

        self.params = params

        # TODO - check if it's test
        # (mihgen) Will do it right when config file of new Nailgun available
        if True:
            self.params['transport'] = 'memory'
            self.memory_transport = True
        else:
            self.memory_transport = False

        self.connection = None
        self.reconnect()

    def _connect(self):
        """Connect to rabbit.  Re-establish any queues that may have
        been declared before if we are reconnecting.  Exceptions should
        be handled by the caller.
        """
        if self.connection:
            LOG.info("Reconnecting to AMQP server on "
                    "%(hostname)s:%(port)d" % self.params)
            try:
                self.connection.close()
            except self.connection_errors:
                pass
            # Setting this in case the next statement fails, though
            # it shouldn't be doing any network operations, yet.
            self.connection = None
        self.connection = kombu.connection.BrokerConnection(
                **self.params)
        self.connection_errors = self.connection.connection_errors
        if self.memory_transport:
            # Kludge to speed up tests.
            self.connection.transport.polling_interval = 0.0
        self.consumer_num = itertools.count(1)
        self.connection.connect()
        self.channel = self.connection.channel()
        # work around 'memory' transport bug in 1.1.3
        if self.memory_transport:
            self.channel._new_queue('ae.undeliver')
        for consumer in self.consumers:
            consumer.reconnect(self.channel)
        LOG.info('Connected to AMQP server on '
                '%(hostname)s:%(port)d' % self.params)

    def reconnect(self):
        """Handles reconnecting and re-establishing queues.
        Will retry up to self.max_retries number of times.
        self.max_retries = 0 means to retry forever.
        Sleep between tries, starting at self.interval_start
        seconds, backing off self.interval_stepping number of seconds
        each attempt.
        """

        attempt = 0
        while True:
            attempt += 1
            try:
                self._connect()
                return
            except (self.connection_errors, IOError), e:
                pass
            except Exception, e:
                # NOTE(comstud): Unfortunately it's possible for amqplib
                # to return an error not covered by its transport
                # connection_errors in the case of a timeout waiting for
                # a protocol response.  (See paste link in LP888621)
                # So, we check all exceptions for 'timeout' in them
                # and try to reconnect in this case.
                if 'timeout' not in str(e):
                    raise

            log_info = {}
            log_info['err_str'] = str(e)
            log_info['max_retries'] = self.max_retries
            log_info.update(self.params)

            if self.max_retries and attempt == self.max_retries:
                LOG.exception('Unable to connect to AMQP server on '
                        '%(hostname)s:%(port)d after %(max_retries)d '
                        'tries: %(err_str)s' % log_info)
                # NOTE(comstud): Copied from original code.  There's
                # really no better recourse because if this was a queue we
                # need to consume on, we have no way to consume anymore.
                sys.exit(1)

            if attempt == 1:
                sleep_time = self.interval_start or 1
            elif attempt > 1:
                sleep_time += self.interval_stepping
            if self.interval_max:
                sleep_time = min(sleep_time, self.interval_max)

            log_info['sleep_time'] = sleep_time
            LOG.exception('AMQP server on %(hostname)s:%(port)d is'
                    ' unreachable: %(err_str)s. Trying again in '
                    '%(sleep_time)d seconds.' % log_info)
            time.sleep(sleep_time)

    def ensure(self, error_callback, method, *args, **kwargs):
        while True:
            try:
                return method(*args, **kwargs)
            except (self.connection_errors, socket.timeout, IOError), e:
                pass
            except Exception, e:
                # NOTE(comstud): Unfortunately it's possible for amqplib
                # to return an error not covered by its transport
                # connection_errors in the case of a timeout waiting for
                # a protocol response.  (See paste link in LP888621)
                # So, we check all exceptions for 'timeout' in them
                # and try to reconnect in this case.
                if 'timeout' not in str(e):
                    raise
            if error_callback:
                error_callback(e)
            self.reconnect()

    def get_channel(self):
        """Convenience call for bin/clear_rabbit_queues"""
        return self.channel

    def close(self):
        """Close/release this connection"""
        self.cancel_consumer_thread()
        self.connection.release()
        self.connection = None

    def reset(self):
        """Reset a connection so it can be used again"""
        self.cancel_consumer_thread()
        self.channel.close()
        self.channel = self.connection.channel()
        # work around 'memory' transport bug in 1.1.3
        if self.memory_transport:
            self.channel._new_queue('ae.undeliver')
        self.consumers = []

    def declare_consumer(self, consumer_cls, topic, callback):
        """Create a Consumer using the class that was passed in and
        add it to our list of consumers
        """

        def _connect_error(exc):
            log_info = {'topic': topic, 'err_str': str(exc)}
            LOG.error("Failed to declare consumer for topic '%(topic)s': "
                "%(err_str)s" % log_info)

        def _declare_consumer():
            consumer = consumer_cls(self.channel, topic, callback,
                    self.consumer_num.next())
            self.consumers.append(consumer)
            return consumer

        return self.ensure(_connect_error, _declare_consumer)

    def iterconsume(self, limit=None, timeout=None):
        """Return an iterator that will consume from all queues/consumers"""

        info = {'do_consume': True}

        def _error_callback(exc):
            if isinstance(exc, socket.timeout):
                LOG.exception('Timed out waiting for RPC response: %s' %
                        str(exc))
                #raise rpc_common.Timeout()
                raise Exception("Timed out waiting for RPC response: %s" % \
                        str(exc))
            else:
                LOG.exception('Failed to consume message from queue: %s' %
                        str(exc))
                raise
                info['do_consume'] = True

        def _consume():
            if info['do_consume']:
                queues_head = self.consumers[:-1]
                queues_tail = self.consumers[-1]
                for queue in queues_head:
                    queue.consume(nowait=True)
                queues_tail.consume(nowait=False)
                info['do_consume'] = False
            return self.connection.drain_events(timeout=timeout)

        for iteration in itertools.count(0):
            if limit and iteration >= limit:
                raise StopIteration
            yield self.ensure(_error_callback, _consume)

    def cancel_consumer_thread(self):
        """Cancel a consumer thread"""
        if self.consumer_thread is not None:
            self.consumer_thread.kill()
            try:
                self.consumer_thread.wait()
            except greenlet.GreenletExit:
                pass
            self.consumer_thread = None

    def publisher_send(self, cls, topic, msg, **kwargs):
        """Send to a publisher based on the publisher class"""

        def _error_callback(exc):
            log_info = {'topic': topic, 'err_str': str(exc)}
            LOG.exception("Failed to publish message to topic "
                "'%(topic)s': %(err_str)s" % log_info)

        def _publish():
            publisher = cls(self.channel, topic, **kwargs)
            publisher.send(msg)

        self.ensure(_error_callback, _publish)

    def declare_direct_consumer(self, topic, callback):
        """Create a 'direct' queue.
        This is generally a msg_id queue used for
        responses for call/multicall
        """
        self.declare_consumer(DirectConsumer, topic, callback)

    def declare_topic_consumer(self, topic, callback=None):
        """Create a 'topic' consumer."""
        self.declare_consumer(TopicConsumer, topic, callback)

    def direct_send(self, msg_id, msg):
        """Send a 'direct' message"""
        self.publisher_send(DirectPublisher, msg_id, msg)

    def topic_send(self, topic, msg):
        """Send a 'topic' message"""
        self.publisher_send(TopicPublisher, topic, msg)

    def consume(self, limit=None):
        """Consume from all queues/consumers"""
        it = self.iterconsume(limit=limit)
        while True:
            try:
                it.next()
            except StopIteration:
                return

    def consume_in_thread(self):
        """Consumer from all queues/consumers in a greenthread"""
        def _consumer_thread():
            try:
                self.consume()
            except greenlet.GreenletExit:
                return
        if self.consumer_thread is None:
            self.consumer_thread = eventlet.spawn(_consumer_thread)

        return self.consumer_thread

    def create_consumer(self, topic, proxy, fanout=False):
        """Create a consumer that calls a method in a proxy object"""
        if fanout:
            self.declare_fanout_consumer(topic,
                    rpc_amqp.ProxyCallback(proxy, Connection.pool))
        else:
            self.declare_topic_consumer(topic,
                    rpc_amqp.ProxyCallback(proxy, Connection.pool))


Connection.pool = rpc_amqp.Pool(connection_cls=Connection)


def create_connection(new=True):
    """Create a connection"""
    return rpc_amqp.create_connection(new, Connection.pool)


def call(topic, msg, timeout=None):
    """Sends a message on a topic and wait for a response."""
    return rpc_amqp.call(topic, msg, timeout, Connection.pool)


def cast(topic, msg):
    """Sends a message on a topic without waiting for a response."""
    return rpc_amqp.cast(topic, msg, Connection.pool)


def cleanup():
    return rpc_amqp.cleanup(Connection.pool)
