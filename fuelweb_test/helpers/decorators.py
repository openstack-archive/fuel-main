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
import os
import time
import traceback
import urllib2

from time import sleep

from devops.helpers.helpers import SSHClient
from devops.helpers import helpers
from proboscis import SkipTest

from fuelweb_test import settings
from fuelweb_test import logger


def save_logs(url, filename):
    logger.info('Saving logs to "{}" file'.format(filename))
    try:
        with open(filename, 'w') as f:
            f.write(
                urllib2.urlopen(url).read()
            )
    except (urllib2.HTTPError, urllib2.URLError) as e:
        logger.error(e)


def log_snapshot_on_error(func):
    """Snapshot environment in case of error.

    Decorator to snapshot environment when error occurred in test.
    And always fetch diagnostic snapshot from master node
    """
    @functools.wraps(func)
    def wrapper(*args, **kwagrs):
        try:
            return func(*args, **kwagrs)
        except SkipTest:
            raise SkipTest()
        except Exception:
            if args and 'snapshot' in args[0].__dict__:
                name = 'error_%s' % args[0].snapshot
                description = "Failed in method '%s'." % args[0].snapshot
            else:
                name = 'error_%s' % func.__name__
                description = "Failed in method '%s'." % func.__name__
            if args[0].env is not None:
                try:
                    create_diagnostic_snapshot(args[0].env,
                                               "fail", name)
                except:
                    logger.error(traceback.format_exc())
                    raise
                finally:
                    logger.debug(args)
                    args[0].env.make_snapshot(snapshot_name=name[-50:],
                                              description=description,
                                              is_make=True)
            raise
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
                logger.info("Uploading new manifests from %s" %
                            settings.UPLOAD_MANIFESTS_PATH)
                remote = SSHClient(args[0].admin_node_ip,
                                   username='root',
                                   password='r00tme')
                remote.execute('rm -rf /etc/puppet/modules/*')
                remote.upload(settings.UPLOAD_MANIFESTS_PATH,
                              '/etc/puppet/modules/')
                logger.info("Copying new site.pp from %s" %
                            settings.SITEPP_FOR_UPLOAD)
                remote.execute("cp %s /etc/puppet/manifests" %
                               settings.SITEPP_FOR_UPLOAD)
        except Exception:
            logger.error("Could not upload manifests")
            raise
        return result
    return wrapper


def revert_info(snapshot_name, description=""):
    logger.info("<" * 5 + "*" * 100 + ">" * 5)
    logger.info("{} Make snapshot: {}".format(description, snapshot_name))
    logger.info("You could revert this snapshot using [{command}]".format(
        command="dos.py revert {env} --snapshot-name {name} && "
        "dos.py resume {env} && virsh net-dumpxml {env}_admin | "
        "grep -P {pattern} -o "
        "| awk {awk_command}".format(
            env=settings.ENV_NAME,
            name=snapshot_name,
            pattern="\"(\d+\.){3}\"",
            awk_command="'{print \"Admin node IP: \"$0\"2\"}'"
        )
    )
    )

    logger.info("<" * 5 + "*" * 100 + ">" * 5)


def update_ostf(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        try:
            if settings.UPLOAD_PATCHSET:
                if not settings.GERRIT_REFSPEC:
                    raise ValueError('REFSPEC should be set for CI tests.')
                logger.info("Uploading new patchset from {0}"
                            .format(settings.GERRIT_REFSPEC))
                remote = SSHClient(args[0].admin_node_ip,
                                   username='root',
                                   password='r00tme')
                remote.upload(settings.PATCH_PATH.rstrip('/'),
                              '/tmp/fuel-ostf')
                remote.execute('source /opt/fuel_plugins/ostf/bin/activate; '
                               'cd /tmp/fuel-ostf; python setup.py develop')
                remote.execute('/etc/init.d/supervisord restart')
                helpers.wait(
                    lambda: "RUNNING" in
                    remote.execute("supervisorctl status ostf | awk\
                                   '{print $2}'")['stdout'][0],
                    timeout=60)
                logger.info("OSTF status: RUNNING")
        except Exception as e:
            logger.error("Could not upload patch set {e}".format(e=e))
            raise
        return result
    return wrapper


def create_diagnostic_snapshot(env, status, name=""):
    task = env.fuel_web.task_wait(env.fuel_web.client.generate_logs(), 60 * 5)
    url = "http://{}:8000{}".format(
        env.get_admin_node_ip(), task['message']
    )
    log_file_name = '{status}_{name}-{time}.tar.gz'.format(
        status=status,
        name=name,
        time=time.strftime("%Y_%m_%d__%H_%M_%S", time.gmtime())
    )
    save_logs(url, os.path.join(settings.LOGS_DIR, log_file_name))


def retry(count=3, delay=30):
    def wrapped(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            i = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except:
                    i += 1
                    if i >= count:
                        raise
                    sleep(delay)
        return wrapper
    return wrapped


def custom_repo(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from fuelweb_test.helpers.regenerate_repo import CustomRepo
        try:
            if settings.CUSTOM_PKGS_MIRROR:
                custom_pkgs = CustomRepo()
                custom_pkgs.prepare_repository()

        except Exception:
            logger.error("Unable to get custom packets from {0}\n{1}"
                         .format(settings.CUSTOM_PKGS_MIRROR,
                                 traceback.format_exc()))
            raise

        result = func(*args, **kwargs)
        return result
    return wrapper
