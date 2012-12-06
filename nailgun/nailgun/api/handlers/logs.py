# -*- coding: utf-8 -*-

import os.path
import json
import logging

import web

from nailgun.settings import settings
from nailgun.api.models import Node
from nailgun.api.handlers.base import JSONHandler


class LogEntryCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        user_data = web.input()
        if not user_data.node or not user_data.source:
            raise web.badrequest()

        node = web.ctx.orm.query(Node).get(user_data.node)
        if not node:
            return web.notfound()

        log_config = filter(lambda lc: lc['id'] == user_data.source,
                            settings.REMOTE_LOGS)
        if not log_config:
            return web.notfound()
        log_config = log_config[0]

        node_log_dir = os.path.join(settings.REMOTE_LOGS_PATH, node.ip)
        if not os.path.exists(node_log_dir):
            return web.notfound()

        node_log_file = os.path.join(node_log_dir, log_config['path'])
        if not os.path.exists(node_log_file):
            return web.notfound()

        output = []
        f = open(node_log_file, 'r')
        for line in f:
            output.append({
                'date': '123',
                'level': 'INFO',
                'text': line.strip()
            })
        f.close()
        return json.dumps(output)

class LogSourceCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        return json.dumps(settings.REMOTE_LOGS, indent=4)
