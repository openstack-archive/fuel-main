# -*- coding: utf-8 -*-

import re
import os.path
import json
import logging

import web

from nailgun.settings import settings
from nailgun.api.models import Node
from nailgun.api.handlers.base import JSONHandler

logger = logging.getLogger(__name__)


class LogEntryCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        user_data = web.input()
        if not user_data.get('node') or not user_data.get('source'):
            raise web.badrequest("'node' and 'source' must be specified")

        node = web.ctx.orm.query(Node).get(user_data.node)
        if not node:
            return web.notfound("Node not found")
        if not node.ip:
            return web.internalerror("Node has no assigned ip")

        log_config = filter(lambda lc: lc['id'] == user_data.source,
                            settings.REMOTE_LOGS)
        if not log_config:
            return web.notfound("Log source not found")
        log_config = log_config[0]

        node_log_dir = os.path.join(settings.REMOTE_LOGS_PATH, node.ip)
        if not os.path.exists(node_log_dir):
            return web.notfound("Log file not found")

        node_log_file = os.path.join(node_log_dir, log_config['path'])
        if not os.path.exists(node_log_file):
            return web.notfound("Log file not found")

        output = []
        f = open(node_log_file, 'r')
        for line in f:
            entry = line.rstrip('\n')
            m = re.match(settings.REMOTE_LOGS_REGEXP, entry)
            if m is None:
                logger.error("Unable to parse log entry '%s'" % entry)
                continue
            output.append({
                'date': m.group('date'),
                'level': m.group('level') or 'INFO',
                'text': m.group('text')
            })
        f.close()
        return json.dumps(output)


class LogSourceCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        return json.dumps(settings.REMOTE_LOGS, indent=4)
