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

from devops.helpers.helpers import SSHClient
from proboscis import SkipTest

from fuelweb_test import settings


def save_logs(url, filename):
    logging.info('Saving logs to "{}" file'.format(filename))
    try:
        with open(filename, 'w') as f:
            f.write(
                urllib2.urlopen(url).read()
            )
    except urllib2.HTTPError as e:
        logging.error(e)


def log_snapshot_on_error(func):
    """Snapshot environment in case of error.

    Decorator to snapshot environment when error occurred in test.
    And always fetch diagnostic snapshot from master node
    """
    @functools.wraps(func)
    def wrapper(*args, **kwagrs):
        status = "pass"
        try:
            return func(*args, **kwagrs)
        except SkipTest:
            pass
        except Exception:
            status = "fail"
            name = 'error_%s' % func.__name__
            description = "Failed in method '%s'." % func.__name__
            logging.info("<" * 5 + "*" * 100 + ">" * 5)
            logging.info("{} Make snapshot: {}".format(description, name))
            logging.info(
                "You could revert this snapshot using [{command}]".format(
                    command="dos.py revert {env} --snapshot-name {name} && "
                    "dos.py resume {env} && "
                    "virsh net-dumpxml {env}_admin | grep -P {pattern} -o "
                    "| awk {awk_command}".format(
                        env=settings.ENV_NAME, name=name,
                        pattern="\"(\d+\.){3}\"",
                        awk_command="'{print \"Admin node IP: \"$0\"2\"}'"
                    )
                )
            )
            logging.info("<" * 5 + "*" * 100 + ">" * 5)
            if args[0].env is not None:
                args[0].env.make_snapshot(snapshot_name=name[-50:])
            raise
        finally:
            if settings.LOGS_DIR:
                if not os.path.exists(settings.LOGS_DIR):
                    os.makedirs(settings.LOGS_DIR)

                env = args[0].env
                env.get_virtual_environment().resume()
                task = env.fuel_web.client.generate_logs()
                task = env.fuel_web.task_wait(task, 60 * 5)
                url = "http://{}:8000{}".format(
                    env.get_admin_node_ip(), task['message']
                )
                log_file_name = '{status}_{name}-{time}.tar.gz'.format(
                    status=status,
                    name=func.__name__,
                    time=time.strftime("%Y_%m_%d__%H_%M_%S", time.gmtime())
                )
                save_logs(url, os.path.join(settings.LOGS_DIR, log_file_name))
    return wrapper


def debug(logger):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            logger.debug(
                "Calling: {} with args: {} {}".format(
                    func.__name__, args, kwargs
                )
            )
            result = func(*args, **kwargs)
            logger.debug(
                "Done: {} with result: {}".format(func.__name__, result))
            return result
        return wrapped
    return wrapper


def json_parse(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        response = func(*args, **kwargs)
        return json.loads(response.read())
    return wrapped


def upload_manifests(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        try:
            if settings.UPLOAD_MANIFESTS:
                logging.info("Uploading new manifests from %s" %
                             settings.UPLOAD_MANIFESTS_PATH)
                remote = SSHClient(args[0].admin_node_ip,
                                   username='root',
                                   password='r00tme')
                remote.execute('rm -rf /etc/puppet/modules/*')
                remote.upload(settings.UPLOAD_MANIFESTS_PATH,
                              '/etc/puppet/modules/')
                logging.info("Copying new site.pp from %s" %
                             settings.SITEPP_FOR_UPLOAD)
                remote.execute("cp %s /etc/puppet/manifests" %
                               settings.SITEPP_FOR_UPLOAD)
        except Exception:
            logging.error("Could not upload manifests")
            raise
        return result
    return wrapper
