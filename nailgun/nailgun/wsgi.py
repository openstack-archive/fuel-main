import os
import sys
import web

curdir = os.path.dirname(__file__)
sys.path.insert(0, curdir)

from nailgun.settings import settings
from nailgun.api.handlers import check_client_content_type
from nailgun.api.handlers import forbid_client_caching
from nailgun.db import load_db_driver, engine
from nailgun.urls import urls
from nailgun.logger import logger, FileLoggerMiddleware, HTTPLoggerMiddleware


class FlushingLogger(object):
    def __init__(self):
        self.opened = False
        self.fd = None

    @property
    def _fd(self):
        if not self.opened:
            self.fd = open(settings.ACCESS_LOG, "a+")
            self.opened = True
        return self.fd

    def __enter__(self):
        return self._fd

    def __exit__(self, type, value, traceback):
        self._fd.close()
        self.opened = False

    def write(self, data):
        self._fd.write(data)
        self._fd.flush()

    def close(self):
        self._fd.close()
        self.opened = False


def build_app():
    app = web.application(urls, locals())
    app.add_processor(load_db_driver)
    app.add_processor(forbid_client_caching)
    return app


def build_middleware(app):
    middleware_list = [
        HTTPLoggerMiddleware,
    ]
    if not int(settings.DEVELOPMENT):
        middleware_list.append(FileLoggerMiddleware)

    logger.debug('Initialize middleware: %s' %
                 (map(lambda x: x.__name__, middleware_list)))

    return app(*middleware_list)


def appstart(keepalive=False):
    logger.info("Fuel-Web {0} ({1})".format(
        settings.PRODUCT_VERSION,
        settings.COMMIT_SHA
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

    web.httpserver.runsimple(
        wsgifunc,
        (
            settings.LISTEN_ADDRESS,
            int(settings.LISTEN_PORT)
        )
    )
    logger.info("Stopping WSGI app...")
    if keep_alive.is_alive():
        logger.info("Stopping KeepAlive watcher...")
        keep_alive.join()
    if not settings.FAKE_TASKS:
        logger.info("Stopping RPC consumer...")
        rpc_process.join()
    logger.info("Done")
