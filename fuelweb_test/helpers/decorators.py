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
import inspect
import json
import os
import sys
import time
import traceback
import urllib2

from os.path import expanduser

from devops.helpers import helpers
from fuelweb_test.helpers.checkers import check_action_logs
from fuelweb_test.helpers.checkers import check_stats_on_collector
from fuelweb_test.helpers.checkers import check_stats_private_info
from fuelweb_test.helpers.checkers import count_stats_on_collector
from proboscis import SkipTest
from proboscis.asserts import assert_equal

from fuelweb_test import logger
from fuelweb_test import settings
from fuelweb_test.helpers.regenerate_repo import CustomRepo
from fuelweb_test.helpers.utils import pull_out_logs_via_ssh
from fuelweb_test.helpers.utils import store_astute_yaml


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
    def wrapper(*args, **kwargs):
        logger.info("\n" + "<" * 5 + "#" * 30 + "[ {} ]"
                    .format(func.__name__) + "#" * 30 + ">" * 5 + "\n{}"
                    .format(func.__doc__))
        try:
            return func(*args, **kwargs)
        except SkipTest:
            raise SkipTest()
        except Exception as test_exception:
            exc_trace = sys.exc_traceback
            name = 'error_%s' % func.__name__
            description = "Failed in method '%s'." % func.__name__
            if args[0].env is not None:
                try:
                    create_diagnostic_snapshot(args[0].env,
                                               "fail", name)
                except:
                    logger.error("Fetching of diagnostic snapshot failed: {0}".
                                 format(traceback.format_exc()))
                    try:
                        admin_remote = args[0].env.get_admin_remote()
                        pull_out_logs_via_ssh(admin_remote, name)
                    except:
                        logger.error("Fetching of raw logs failed: {0}".
                                     format(traceback.format_exc()))
                finally:
                    logger.debug(args)
                    try:
                        args[0].env.make_snapshot(snapshot_name=name[-50:],
                                                  description=description,
                                                  is_make=True)
                    except:
                        logger.error("Error making the environment snapshot:"
                                     " {0}".format(traceback.format_exc()))
            raise test_exception, None, exc_trace
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
                if args[0].__class__.__name__ == "EnvironmentModel":
                    environment = args[0]
                elif args[0].__class__.__name__ == "FuelWebClient":
                    environment = args[0].environment
                else:
                    logger.warning("Can't upload manifests: method of "
                                   "unexpected class is decorated.")
                    return result
                remote = environment.get_admin_remote()
                remote.execute('rm -rf /etc/puppet/modules/*')
                remote.upload(settings.UPLOAD_MANIFESTS_PATH,
                              '/etc/puppet/modules/')
                logger.info("Copying new site.pp from %s" %
                            settings.SITEPP_FOR_UPLOAD)
                remote.execute("cp %s /etc/puppet/manifests" %
                               settings.SITEPP_FOR_UPLOAD)
                if settings.SYNC_DEPL_TASKS:
                    remote.execute("fuel release --sync-deployment-tasks"
                                   " --dir /etc/puppet/")
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
                remote = args[0].environment.get_admin_remote()
                remote.upload(settings.PATCH_PATH.rstrip('/'),
                              '/var/www/nailgun/fuel-ostf')
                remote.execute('dockerctl shell ostf '
                               'bash -c "cd /var/www/nailgun/fuel-ostf; '
                               'python setup.py develop"')
                remote.execute('dockerctl shell ostf '
                               'bash -c "supervisorctl restart ostf"')
                helpers.wait(
                    lambda: "0" in
                    remote.execute('dockerctl shell ostf '
                                   'bash -c "pgrep [o]stf; echo $?"')
                    ['stdout'][1], timeout=60)
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
                    time.sleep(delay)
        return wrapper
    return wrapped


def custom_repo(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        custom_pkgs = CustomRepo(args[0].environment)
        try:
            if settings.CUSTOM_PKGS_MIRROR:
                custom_pkgs.prepare_repository()

        except Exception:
            logger.error("Unable to get custom packages from {0}\n{1}"
                         .format(settings.CUSTOM_PKGS_MIRROR,
                                 traceback.format_exc()))
            raise

        try:
            return func(*args, **kwargs)
        except Exception:
            custom_pkgs.check_puppet_logs()
            raise
    return wrapper


def check_fuel_statistics(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if not settings.FUEL_STATS_CHECK:
            return result
        logger.info('Test "{0}" passed. Checking stats.'.format(func.__name__))
        fuel_settings = args[0].env.get_fuel_settings()
        nailgun_actions = args[0].env.nailgun_actions
        postgres_actions = args[0].env.postgres_actions
        remote_collector = args[0].env.get_ssh_to_remote_by_key(
            settings.FUEL_STATS_HOST,
            '{0}/.ssh/id_rsa'.format(expanduser("~")))
        master_uuid = args[0].env.get_masternode_uuid()
        logger.info("Master Node UUID: '{0}'".format(master_uuid))
        nailgun_actions.force_fuel_stats_sending()

        if not settings.FUEL_STATS_ENABLED:
            assert_equal(0, int(count_stats_on_collector(remote_collector,
                                                         master_uuid)),
                         "Sending of Fuel stats is disabled in test, but "
                         "usage info was sent to collector!")
            assert_equal(args[0].env.postgres_actions.count_sent_action_logs(),
                         0, ("Sending of Fuel stats is disabled in test, but "
                             "usage info was sent to collector!"))
            return result

        test_scenario = inspect.getdoc(func)
        if 'Scenario' not in test_scenario:
            logger.warning(("Can't check that fuel statistics was gathered "
                            "and sent to collector properly because '{0}' "
                            "test doesn't contain correct testing scenario. "
                            "Skipping...").format(func.__name__))
            return func(*args, **kwargs)
        try:
            check_action_logs(test_scenario, postgres_actions)
            check_stats_private_info(remote_collector,
                                     postgres_actions,
                                     master_uuid,
                                     fuel_settings)
            check_stats_on_collector(remote_collector,
                                     postgres_actions,
                                     master_uuid)
            return result
        except Exception:
            logger.error(traceback.format_exc())
            raise
    return wrapper


def download_astute_yaml(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if settings.STORE_ASTUTE_YAML:
            store_astute_yaml(args[0].env)
        return result
    return wrapper
