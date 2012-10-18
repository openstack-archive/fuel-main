#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
import code

import web
from sqlalchemy.orm import scoped_session, sessionmaker

from nailgun.api.handlers import check_client_content_type
from nailgun.api.models import engine
from nailgun.db import load_db_driver, syncdb
from nailgun.unit_test import TestRunner
from nailgun.urls import urls
from nailgun.logger import Log
from nailgun.wsgi import app


logging.basicConfig(level="DEBUG")


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
    runwsgi_parser = subparsers.add_parser(
        'runwsgi', help='run WSGI application'
    )
    runwsgi_parser.add_argument(
        '-p', '--port', dest='port', action='store', type=str,
        help='application port', default='8000'
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
        logging.info("Syncing database...")
        syncdb()
        logging.info("Done")
    elif params.action == "test":
        logging.info("Running tests...")
        TestRunner.run()
        logging.info("Done")
    elif params.action == "loaddata":
        from nailgun.fixtures import fixman
        if os.path.exists(params.fixture):
            logging.info("Uploading fixtures...")
            with open(params.fixture, "r") as f:
                fixman.upload_fixture(f)
            logging.info("Done")
        else:
            parser.print_help()
    elif params.action in ("run", "runwsgi"):
        from nailgun.rpc import threaded
        import eventlet
        eventlet.monkey_patch()
        q = threaded.rpc_queue
        rpc_thread = threaded.RPCThread()

        if params.action == "run":
            app = web.application(urls, locals(), autoreload=True)
        else:
            app = web.application(urls, locals())

        app.add_processor(load_db_driver)
        app.add_processor(check_client_content_type)

        if params.action == "run":
            sys.argv.insert(1, params.port)
            app.run()
        else:
            logging.info("Running WSGI app...")
            server = web.httpserver.WSGIServer(
                ("0.0.0.0", int(params.port)),
                app.wsgifunc(Log)
            )
            try:
                rpc_thread.start()
                server.start()
            except KeyboardInterrupt:
                logging.info("Stopping RPC thread...")
                rpc_thread.running = False
                logging.info("Stopping WSGI app...")
                server.stop()
                logging.info("Done")
    elif params.action == "shell":
        orm = scoped_session(sessionmaker(bind=engine))
        code.interact(local={'orm': orm})
        orm.commit()
    else:
        parser.print_help()
