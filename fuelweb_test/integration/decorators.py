#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import functools
import json
import logging
import os
import time
import urllib2
from fuelweb_test.settings import LOGS_DIR


def save_logs(url, filename):
    logging.info('Saving logs to "%s" file' % filename)
    try:
        with open(filename, 'w') as f:
            f.write(
                urllib2.urlopen(url).read()
            )
    except urllib2.HTTPError, e:
        logging.error(e)


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

                test_case = args[0]
                task = test_case.client.generate_logs()
                task = test_case._task_wait(task, 60 * 5)
                url = "http://%s:8000%s" % \
                      (test_case.get_admin_node_ip(), task['message'])

                save_logs(
                    url,
                    os.path.join(LOGS_DIR, '%s-%d.tar.gz' % (
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
            name = 'error-%s' % func.__name__
            description = "Failed in method '%s'" % func.__name__
            logging.debug("Snapshot %s %s" % (name, description))
            if args[0].ci() is not None:
                args[0].ci().environment().suspend(verbose=False)
                args[0].ci().environment().snapshot(
                    name=name[-50:],
                    description=description,
                    force=True,
                )
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
