import functools
import json
import logging
import os
import time
import urllib2
from fuelweb_test.settings import LOGS_DIR


def save_logs(ip, filename):
    logging.info('Saving logs to "%s" file' % filename)
    with open(filename, 'w') as f:
        f.write(
            urllib2.urlopen("http://%s:8000/api/logs/package" % ip).read()
        )


def fetch_logs(func):
    """ Decorator to fetch logs to file.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwagrs):
        # noinspection PyBroadException
        try:
            return func(*args, **kwagrs)
        finally:
            if LOGS_DIR:
                if not os.path.exists(LOGS_DIR):
                    os.makedirs(LOGS_DIR)
                save_logs(
                    args[0].get_admin_node_ip(),
                    os.path.join(LOGS_DIR, '{%s}-{%s}' % (
                        func.__name__,
                        time.time())))
    return wrapper


def snapshot_errors(func):
    """ Decorator to snapshot environment when error occurred in test.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwagrs):
        try:
            return func(*args, **kwagrs)
        except:
            name = 'error-%s' % time.time()
            description = "Failed in method '%s'" % func.__name__
            logging.debug("Snapshot %s %s" % (name, description))
            if args[0].ci() is not None:
                args[0].ci().environment().suspend(verbose=False)
                args[0].ci().environment().snapshot(name, description)
            raise
    return wrapper


def debug(logger):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            logger.debug(
                "Calling: %s with args: %s %s" % (func.__name__, args, kwargs))
            result = func(*args, **kwargs)
            logger.debug("Done: %s with result: %s" % (func.__name__, result))
            return result
        return wrapped
    return wrapper


def json_parse(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        response = func(*args, **kwargs)
        return json.loads(response.read())
    return wrapped
