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
        if not user_data.get('source'):
            raise web.badrequest("'source' must be specified")

        log_config = filter(lambda lc: lc['id'] == user_data.source,
                            settings.LOGS)
        if not log_config:
            return web.notfound("Log source not found")
        log_config = log_config[0]

        if log_config['remote']:
            if not user_data.get('node'):
                raise web.badrequest("'node' must be specified")
            node = web.ctx.orm.query(Node).get(user_data.node)
            if not node:
                return web.notfound("Node not found")
            if not node.ip:
                return web.internalerror("Node has no assigned ip")

            remote_log_dir = os.path.join(log_config['base'], node.ip)
            if not os.path.exists(remote_log_dir):
                return web.notfound("Log files dir for node not found")

            log_file = os.path.join(remote_log_dir, log_config['path'])
        else:
            log_file = log_config['path']
        if not os.path.exists(log_file):
            return web.notfound("Log file not found")

        output = []
        from_line = 0
        try:
            from_line = int(user_data.get('from', 0))
        except ValueError:
            raise web.badrequest("Invalid 'from' value")

        with open(log_file, 'r') as f:
            for num, line in enumerate(f):
                if num < from_line:
                    continue
                entry = line.rstrip('\n')
                if not len(entry):
                    continue
                m = re.match(log_config['regexp'], entry)
                if m is None:
                    logger.error("Unable to parse log entry '%s'" % entry)
                    continue
                output.append([
                    m.group('date'),
                    m.group('level') or 'INFO',
                    m.group('text')
                ])

        return json.dumps(output)


class LogSourceCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        return json.dumps(settings.LOGS, indent=4)
