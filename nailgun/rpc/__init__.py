from rpc import impl_kombu as impl


def create_connection(new=True):
    """Create a connection to the message bus used for rpc.

    For some example usage of creating a connection and some consumers on that
    connection, see nailgun.service.

    :param new: Whether or not to create a new connection.  A new connection
                will be created by default.  If new is False, the
                implementation is free to return an existing connection from a
                pool.

    :returns: An instance of nailgun.rpc.impl_kombu.Connection
    """
    return impl.create_connection(new=new)


def call(topic, msg, timeout=None):
    """Invoke a remote method that returns something.

    :param topic: The topic to send the rpc message to.  This correlates to the
                  topic argument of
                  nailgun.rpc.impl_kombu.Connection.create_consumer() and only
                  applies when the consumer was created with fanout=False.
    :param msg: This is a dict in the form { "method" : "method_to_invoke",
                                             "args" : dict_of_kwargs }
    :param timeout: int, number of seconds to use for a response timeout.
                    If set, this overrides the rpc_response_timeout option.

    :returns: A dict from the remote method.

    :raises: nailgun.rpc.impl_kombu.Timeout if a complete response is not
             received before the timeout is reached.
    """
    return impl.call(topic, msg, timeout)


def cast(topic, msg):
    """Invoke a remote method that does not return anything.

    :param topic: The topic to send the rpc message to.  This correlates to the
                  topic argument of
                  nailgun.rpc.impl_kombu.Connection.create_consumer() and only
                  applies when the consumer was created with fanout=False.
    :param msg: This is a dict in the form { "method" : "method_to_invoke",
                                             "args" : dict_of_kwargs }

    :returns: None
    """
    return impl.cast(topic, msg)


def cleanup():
    """Clean up resoruces in use by implementation.

    Clean up any resources that have been allocated by the RPC implementation.
    This is typically open connections to a messaging service.  This function
    would get called before an application using this API exits to allow
    connections to get torn down cleanly.

    :returns: None
    """
    return impl.cleanup()
