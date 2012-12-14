# -*- coding: utf-8 -*-

import re
import os.path
import json
import logging
from itertools import dropwhile

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

        level = user_data.get('level')
        allowed_levels = log_config['levels']
        if level is not None:
            if not (level in log_config['levels']):
                raise web.badrequest("Invalid level")
            allowed_levels = [l for l in dropwhile(lambda l: l != level,
                                                   log_config['levels'])]

        entries = []
        from_byte = 0
        try:
            from_byte = int(user_data.get('from', 0))
        except ValueError:
            raise web.badrequest("Invalid 'from' value")

        with open(log_file, 'r') as f:
            f.seek(from_byte)
            for line in f:
                entry = line.rstrip('\n')
                if not len(entry):
                    continue
                if 'skip_regexp' in log_config and \
                        re.match(log_config['skip_regexp'], entry):
                        continue
                m = re.match(log_config['regexp'], entry)
                if m is None:
                    logger.warn("Unable to parse log entry '%s' from %s",
                                entry, log_file)
                    continue
                entry_level = m.group('level') or 'INFO'
                if level and not (entry_level in allowed_levels):
                    continue
                entries.append([
                    m.group('date'),
                    entry_level,
                    m.group('text')
                ])
            from_byte = f.tell()

        return json.dumps({
            'entries': entries,
            'from': from_byte,
        })


class LogSourceCollectionHandler(JSONHandler):

    def GET(self):
        web.header('Content-Type', 'application/json')
        return json.dumps(settings.LOGS, indent=4)
