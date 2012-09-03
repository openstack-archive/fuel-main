#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import logging
import code

import web

import db
from api.handlers import check_client_content_type
from api.models import engine
from sqlalchemy.orm import scoped_session, sessionmaker
from unit_test import TestRunner
from urls import urls

logging.basicConfig(level="DEBUG")

app = web.application(urls, locals())
app.add_processor(db.load_db_driver)
app.add_processor(check_client_content_type)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="action", help='actions'
    )
    run_parser = subparsers.add_parser(
        'run', help='run application locally'
    )
    runwsgi_parser = subparsers.add_parser(
        'runwsgi', help='run WSGI application'
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
    params, other_params = parser.parse_known_args()
    sys.argv.pop(1)

    if params.action == "syncdb":
        logging.info("Syncing database...")
        db.syncdb()
        logging.info("Done")
    elif params.action == "test":
        logging.info("Running tests...")
        TestRunner.run()
        logging.info("Done")
    elif params.action == "run":
        app.run()
    elif params.action == "runwsgi":
        logging.info("Running WSGI app...")
        server = web.httpserver.WSGIServer(
            ("0.0.0.0", 8080),
            app.wsgifunc()
        )
        try:
            server.start()
        except KeyboardInterrupt:
            logging.info("Stopping WSGI app...")
            server.stop()
            logging.info("Done")
    elif params.action == "shell":
        orm = scoped_session(sessionmaker(bind=engine))
        code.interact(local={'orm': orm})
        orm.commit()
    else:
        parser.print_help()
