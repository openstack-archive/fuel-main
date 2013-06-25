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
events = [
    {'name': 'install',
     'src': state.registered,
     'dst': state.downloading},
    {'name': 'downloading_error',
     'src': state.downloading,
     'dst': state.downloading_error},
    {'name': 'redownload',
     'src': state.downloading_error,
     'dst': state.downloading},
    {'name': 'delete',
     'src': state.downloading_error,
     'dst': state.deleted},
    {'name': 'downloaded',
     'src': state.downloading,
     'dst': state.downloaded},

    {'name': 'initialize',
     'src': state.downloaded,
     'dst': state.initializing},
    {'name': 'initialized',
     'src': state.initializing,
     'dst': state.initialized},
    {'name': 'initializing_error',
     'src': state.initializing,
     'dst': state.initializing_error},
    {'name': 'reinitialize',
     'src': state.initializing_error,
     'dst': state.initializing},
    {'name': 'delete',
     'src': state.initializing_error,
     'dst': state.deleted},
    {'name': 'run',
     'src': state.initialized,
     'dst': state.running},

    {'name': 'stop',
     'src': state.running,
     'dst': state.stopped},
    {'name': 'delete',
     'src': state.stopped,
     'dst': state.deleted},
    {'name': 'run',
     'src': state.stopped,
     'dst': state.running},
]


class PluginFSM(Fysom):
    def __init__(self, plugin_id, current_state, db=None):
        Fysom.__init__(self, {
            'initial': current_state,
            'events': events,
            'callbacks': {
                'oninstall': self.download,
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

    def download(self, event):
        logger.error('*' * 30)
        self.downloaded()

    def initialize(self, event):
        logger.error('*' * 30)
        self.initialized()
