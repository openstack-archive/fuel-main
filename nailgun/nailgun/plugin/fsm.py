# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from fysom import Fysom
from nailgun.api.models import Plugin
from nailgun.db import db
from nailgun.fsm.state_list import StateList
from nailgun.logger import logger
import re


# All possible states
state = StateList(
    'registered',
    'downloading',
    'downloaded',
    'downloading_error',

    'initializing',
    'initialized',
    'initializing_error',

    'running',
    'stopped',
    'deleted',
    'updating'
)

# All possible transactions between events
s = state
events = [
    {'name': 'install',
     'src': s.registered,
     'dst': s.downloading},
    {'name': 'downloading_error',
     'src': s.downloading,
     'dst': s.downloading_error},
    {'name': 'redownload',
     'src': s.downloading_error,
     'dst': s.downloading},
    {'name': 'delete',
     'src': s.downloading_error,
     'dst': s.deleted},
    {'name': 'downloaded',
     'src': s.downloading,
     'dst': s.downloaded},

    {'name': 'initialize',
     'src': s.downloaded,
     'dst': s.initializing},
    {'name': 'initialized',
     'src': s.initializing,
     'dst': s.initialized},
    {'name': 'initializing_error',
     'src': s.initializing,
     'dst': s.initializing_error},
    {'name': 'reinitialize',
     'src': s.initializing_error,
     'dst': s.initializing},
    {'name': 'delete',
     'src': s.initializing_error,
     'dst': s.deleted},
    {'name': 'run',
     'src': s.initialized,
     'dst': s.running},

    {'name': 'stop',
     'src': s.running,
     'dst': s.stopped},
    {'name': 'delete',
     'src': s.stopped,
     'dst': s.deleted},
    {'name': 'run',
     'src': s.stopped,
     'dst': s.running},
]


class PluginFSM(Fysom):
    def __init__(self, plugin_id, current_state):
        Fysom.__init__(self, {
            'initial': current_state,
            'events': events,
            'callbacks': {
                'oninstall': self.install,
                'oninitialize': self.initialize
            }
        })

        self.plugin_id = plugin_id
        self.current_state = current_state
        self.onchangestate = self._onchangestate

    @property
    def is_error(self):
        return bool(re.search('_error$', self.current))

    @property
    def plugin(self):
        return db().query(Plugin).get(self.plugin_id)

    def _onchangestate(self, event):
        logger.debug(
            'Plugin: %s src: %s dst: %s' %
            (self.plugin.name, event.src, event.dst))

        self.plugin.state = event.dst
        db().commit()

    def install(self, event):
        # Downloading
        self.downloaded()

    def initialize(self, event):
        # Initializing
        self.initialized()
