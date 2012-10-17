import os
import sys
import logging

import web

curdir = os.path.dirname(__file__)
sys.path.insert(0, curdir)

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

from nailgun.api.handlers import check_client_content_type
from nailgun.db import load_db_driver
from nailgun.urls import urls

app = web.application(urls, locals())
app.add_processor(load_db_driver)
app.add_processor(check_client_content_type)
application = app.wsgifunc()
