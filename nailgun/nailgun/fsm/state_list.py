# -*- coding: utf-8 -*-

class StateList:
    def __init__(self, *state_list):
        self.state_list = state_list
        self.__dict__.update(dict(zip(state_list, state_list)))

    def all_exclude(self, excluded_states):
        return filter(
            lambda state: not state in excluded_states,
            self.state_list)
