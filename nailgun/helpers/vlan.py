# -*- coding: utf-8 -*-


class VlanManager(object):
    """
    A stub for some real logic in the future
    """
    vlan_ids = {
        'storage': 200,
        'public': 300,
        'floating': 400,
        'fixed': 500,
        'admin': 100
    }

    @classmethod
    def generate_id(cls, name):
        return cls.vlan_ids[name]
