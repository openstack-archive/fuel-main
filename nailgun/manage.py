#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import argparse
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="action", help='actions'
    )
    run_parser = subparsers.add_parser(
        'run', help='run application locally'
    )
    run_parser.add_argument(
        '-p', '--port', dest='port', action='store', type=str,
        help='application port', default='8000'
    )
    run_parser.add_argument(
        '-a', '--address', dest='address', action='store', type=str,
        help='application address', default='0.0.0.0'
    )
    run_parser.add_argument(
        '--fake-tasks', action='store_true', help='fake tasks'
    )
    run_parser.add_argument(
        '--fake-tasks-amqp', action='store_true',
        help='fake tasks with real AMQP'
    )
    run_parser.add_argument(
        '--keepalive',
        action='store_true',
        help='run keep alive thread'
    )
    run_parser.add_argument(
        '-c', '--config', dest='config_file', action='store', type=str,
        help='custom config file', default=None
    )
    run_parser.add_argument(
        '--fake-tasks-tick-count', action='store', type=int,
        help='Fake tasks tick count'
    )
    run_parser.add_argument(
        '--fake-tasks-tick-interval', action='store', type=int,
        help='Fake tasks tick interval in seconds'
    )
    test_parser = subparsers.add_parser(
        'test', help='run unit tests'
    )
    syncdb_parser = subparsers.add_parser(
        'syncdb', help='sync application database'
    )
    dropdb_parser = subparsers.add_parser(
        'dropdb', help='drop application database'
    )
    shell_parser = subparsers.add_parser(
        'shell', help='open python REPL'
    )
    shell_parser.add_argument(
        '-c', '--config', dest='config_file', action='store', type=str,
        help='custom config file', default=None
    )
    loaddata_parser = subparsers.add_parser(
        'loaddata', help='load data from fixture'
    )
    loaddata_parser.add_argument(
        'fixture', action='store', help='json fixture to load'
    )
    dumpdata_parser = subparsers.add_parser(
        'dumpdata', help='dump models as fixture'
    )
    dumpdata_parser.add_argument(
        'model', action='store', help='model name to dump; underscored name'
        'should be used, e.g. network_group for NetworkGroup model'
    )
    loaddefault_parser = subparsers.add_parser(
        'loaddefault',
        help='load data from default fixtures '
             '(settings.FIXTURES_TO_IPLOAD)'
    )
    dump_settings = subparsers.add_parser(
        'dump_settings', help='dump current settings to YAML'
    )
    params, other_params = parser.parse_known_args()
    sys.argv.pop(1)

    if params.action == "dumpdata":
        import logging
        logging.disable(logging.WARNING)
        from nailgun.fixtures import fixman
        fixman.dump_fixture(params.model)
        sys.exit(0)

    from nailgun.logger import logger
    from nailgun.settings import settings

    if params.action == "syncdb":
        logger.info("Syncing database...")
        from nailgun.db import syncdb
        syncdb()
        logger.info("Done")
    elif params.action == "dropdb":
        logger.info("Dropping database...")
        from nailgun.db import dropdb
        dropdb()
        logger.info("Done")
    elif params.action == "test":
        logger.info("Running tests...")
        from nailgun.unit_test import TestRunner
        TestRunner.run()
        logger.info("Done")
    elif params.action == "loaddata":
        logger.info("Uploading fixture...")
        from nailgun.fixtures import fixman
        with open(params.fixture, "r") as fileobj:
            fixman.upload_fixture(fileobj)
        logger.info("Done")
    elif params.action == "loaddefault":
        logger.info("Uploading fixture...")
        from nailgun.fixtures import fixman
        fixman.upload_fixtures()
        logger.info("Done")
    elif params.action == "dump_settings":
        sys.stdout.write(settings.dump())
    elif params.action in ("run",):
        settings.update({
            'LISTEN_PORT': int(params.port),
            'LISTEN_ADDRESS': params.address,
        })
        for attr in ['FAKE_TASKS', 'FAKE_TASKS_TICK_COUNT',
                     'FAKE_TASKS_TICK_INTERVAL', 'FAKE_TASKS_AMQP']:
            param = getattr(params, attr.lower())
            if param is not None:
                settings.update({attr: param})
        if params.config_file:
            settings.update_from_file(params.config_file)
        from nailgun.wsgi import appstart
        appstart(keepalive=params.keepalive)
    elif params.action == "shell":
        if params.config_file:
            settings.update_from_file(params.config_file)
        # try:
        #     from IPython import embed
        #     embed()
        # except ImportError:
        #     code.interact(local={'db': db, 'settings': settings})
    else:
        parser.print_help()
