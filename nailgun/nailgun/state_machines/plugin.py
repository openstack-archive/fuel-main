# -*- coding: utf-8 -*-

from fysom import Fysom
from nailgun.api.models import Plugin
from nailgun.db import orm
from nailgun.logger import logger
import re


class StateList:
    def __init__(self, *state_list):
        self.state_list = state_list
        self.__dict__.update(dict(zip(state_list, state_list)))

    def all_exclude(self, excluded_states):
        return filter(
            lambda state: not state in excluded_states,
            self.state_list)

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
    def __init__(self, plugin_id, current_state, db=None):
        Fysom.__init__(self, {
            'initial': current_state,
            'events': events,
            'callbacks': {
                'oninstall': self.install,
                'oninitialize': self.initialize
            }
        })

        self.db = db or orm()
        self.plugin_id = plugin_id
        self.current_state = current_state
        self.onchangestate = self._onchangestate

    @property
    def is_error(self):
        return bool(re.search('_error$', self.current))

    @property
    def plugin(self):
        return self.db.query(Plugin).get(self.plugin_id)

    def _onchangestate(self, event):
        logger.debug(
            'Plugin: %s src: %s dst: %s' %
            (self.plugin.name, event.src, event.dst))

        self.plugin.state_name = event.dst
        self.db.commit()

    def install(self, event):
        # Downloading
        self.downloaded()

    def initialize(self, event):
        # Initializing
        self.initialized()
