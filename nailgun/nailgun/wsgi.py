import os
import sys
import web
from web.httpserver import server, WSGIServer, StaticMiddleware

curdir = os.path.dirname(__file__)
sys.path.insert(0, curdir)

from nailgun.settings import settings
from nailgun.api.handlers import check_client_content_type
from nailgun.api.handlers import forbid_client_caching
from nailgun.db import load_db_driver, engine
from nailgun.urls import urls
from nailgun.logger import logger, HTTPLoggerMiddleware


def build_app():
    app = web.application(urls, locals())
    app.add_processor(load_db_driver)
    app.add_processor(forbid_client_caching)
    return app


def build_middleware(app):
    middleware_list = [
        HTTPLoggerMiddleware,
    ]

    logger.debug('Initialize middleware: %s' %
                 (map(lambda x: x.__name__, middleware_list)))

    return app(*middleware_list)


def run_server(func, server_address=('0.0.0.0', 8080)):
    """
    This function same as runsimple from web/httpserver
    except removed LogMiddleware because we use
    HTTPLoggerMiddleware instead
    """
    global server
    func = StaticMiddleware(func)
    server = WSGIServer(server_address, func)
    print 'https://%s:%d/' % server_address

    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        server.stop()


def appstart(keepalive=False):
    logger.info("Fuel-Web {0} ({1}/{2})".format(
        settings.PRODUCT_VERSION,
        settings.COMMIT_SHA,
        settings.FUEL_COMMIT_SHA
    ))
    if not engine.dialect.has_table(engine.connect(), "nodes"):
        logger.error(
            "Database tables not created. Try './manage.py syncdb' first"
        )
        sys.exit(1)
    from nailgun.rpc import threaded
    from nailgun.keepalive import keep_alive
    app = build_app()

    if keepalive:
        logger.info("Running KeepAlive watcher...")
        keep_alive.start()

    if not settings.FAKE_TASKS:
        if not keep_alive.is_alive():
            logger.info("Running KeepAlive watcher...")
            keep_alive.start()
        rpc_process = threaded.RPCKombuThread()
        logger.info("Running RPC consumer...")
        rpc_process.start()
    logger.info("Running WSGI app...")

    wsgifunc = build_middleware(app.wsgifunc)

    run_server(wsgifunc,
        (settings.LISTEN_ADDRESS, int(settings.LISTEN_PORT)))

    logger.info("Stopping WSGI app...")
    if keep_alive.is_alive():
        logger.info("Stopping KeepAlive watcher...")
        keep_alive.join()
    if not settings.FAKE_TASKS:
        logger.info("Stopping RPC consumer...")
        rpc_process.join()
    logger.info("Done")
