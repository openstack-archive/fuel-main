# -*- coding: utf-8 -*-

from nailgun.api import urls as api_urls
from nailgun.webui import urls as webui_urls

urls = (
    "/api", api_urls.app,
    "", webui_urls.app
)
