# -*- coding: utf-8 -*-

from api.urls import api_app
from webui.urls import webui_app

urls = (
    "/api", api_app,
    "/", webui_app
)
