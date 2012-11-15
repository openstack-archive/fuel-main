#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import code

import web
from sqlalchemy.orm import scoped_session, sessionmaker

from nailgun.db import syncdb
from nailgun.settings import settings
from nailgun.unit_test import TestRunner
from nailgun.logger import logger


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
    test_parser = subparsers.add_parser(
        'test', help='run unit tests'
    )
    syncdb_parser = subparsers.add_parser(
        'syncdb', help='sync application database'
    )
    shell_parser = subparsers.add_parser(
        'shell', help='open python REPL'
    )
    loaddata_parser = subparsers.add_parser(
        'loaddata', help='load data from fixture'
    )
    loaddata_parser.add_argument(
        'fixture', action='store', help='json fixture to load'
    )
    params, other_params = parser.parse_known_args()
    sys.argv.pop(1)

    if params.action == "syncdb":
        logger.info("Syncing database...")
        syncdb()
        logger.info("Done")
    elif params.action == "test":
        logger.info("Running tests...")
        TestRunner.run()
        logger.info("Done")
    elif params.action == "loaddata":
        logger.info("Uploading fixture...")
        from nailgun.fixtures import fixman
        with open(params.fixture, "r") as fileobj:
            fixman.upload_fixture(fileobj)
        logger.info("Done")
    elif params.action in ("run",):
        settings.update({
            'LISTEN_PORT': int(params.port),
            'LISTEN_ADDRESS': params.address,
        })
        if params.fake_tasks:
            settings.update({'FAKE_TASKS': params.fake_tasks})
        logger.info("Running WSGI app...")
        from nailgun.wsgi import appstart
        appstart()
        logger.info("Stopping WSGI app...")
    elif params.action == "shell":
        from nailgun.api.models import engine
        orm = scoped_session(sessionmaker(bind=engine))
        code.interact(local={'orm': orm})
        orm.commit()
    else:
        parser.print_help()
