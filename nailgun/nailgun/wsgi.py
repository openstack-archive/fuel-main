import os
import sys
import web

curdir = os.path.dirname(__file__)
sys.path.insert(0, curdir)

from nailgun.settings import settings
from nailgun.api.handlers import check_client_content_type
from nailgun.api.handlers import forbid_client_caching
from nailgun.db import load_db_driver
from nailgun.urls import urls
from nailgun.logger import logger, FileLoggerMiddleware


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


def appstart():
    logger.info("Fuel-Web {0} ({1})".format(
        settings.PRODUCT_VERSION,
        settings.COMMIT_SHA
    ))
    from nailgun.rpc import processed
    from nailgun.keepalive import keep_alive
    app = build_app()

    if not settings.FAKE_TASKS:
        logger.info("Running KeepAlive watcher...")
        keep_alive.start()
        rpc_process = processed.RPCProcess()
        logger.info("Running RPC process...")
        rpc_process.start()
    logger.info("Running WSGI app...")
    # seizes control
    if not int(settings.DEVELOPMENT):
        wsgifunc = app.wsgifunc(FileLoggerMiddleware)
    else:
        wsgifunc = app.wsgifunc()
    web.httpserver.runsimple(
        wsgifunc,
        (
            settings.LISTEN_ADDRESS,
            int(settings.LISTEN_PORT)
        )
    )
    logger.info("Stopping WSGI app...")
    if not settings.FAKE_TASKS:
        logger.info("Stopping KeepAlive watcher...")
        keep_alive.join()
        logger.info("Stopping RPC process...")
        rpc_process.terminate()
    logger.info("Done")
