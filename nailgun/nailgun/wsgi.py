import os
import sys
import logging

import web

curdir = os.path.dirname(__file__)
sys.path.insert(0, curdir)

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

from nailgun.settings import settings

from nailgun.api.handlers import check_client_content_type
from nailgun.db import load_db_driver
from nailgun.urls import urls
from nailgun.logger import Log

app = web.application(urls, locals())
app.add_processor(load_db_driver)
app.add_processor(check_client_content_type)


def appstart():
    from nailgun.rpc import threaded
    import eventlet
    eventlet.monkey_patch()
    q = threaded.rpc_queue
    rpc_thread = threaded.RPCThread()
    
    server = web.httpserver.WSGIServer(
        (settings.LISTEN_ADDRESS, int(settings.LISTEN_PORT)),
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

    
application = app.wsgifunc()
