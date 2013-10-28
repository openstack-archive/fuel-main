from collections import namedtuple
import copy
import csv
import os
from datetime import datetime

NODE_INTERFACES = {
    'eth0': ["storage"],
    'eth1': ["public", "floating"],
    'eth2': ["management"],
    'eth3': ["fixed"]
}

ENV_ATTRIBUTES = {
    'editable': {
        'storage': {
            'volumes_lvm': {'value': False},
            'images_ceph': {'value': False},
            'volumes_ceph': {'value': False}
        },
        'additional_components': {
            'savanna': {'value': False},
            'murano': {'value': False}
        }
    }
}

NET = {
    'nova_flat': None,
    'nova_vlan': None,
    'neutron_gre': {
        'net_provider': 'neutron',
        'net_segment_type': 'gre'},
    'neutron_vlan': {
        'net_provider': 'neutron',
        'net_segment_type': 'vlan'}
}

NET_MANAGER_VLAN = {'net_manager': "VlanManager"}

NOVA_NETWORKS_UNTAGGED = {"networks": [
    {'name': "public", 'vlan_start': None},
    {'name': "management", 'vlan_start': None},
    {'name': "storage", 'vlan_start': None},
    {'name': "floating", 'vlan_start': None},
    {'name': "fixed", 'vlan_start': None}
]}
NEUTRON_NETWORK_UNTAGGED = {"networks": [
    {'name': "public", 'vlan_start': None},
    {'name': "management", 'vlan_start': None},
    {'name': "storage", 'vlan_start': None}
]}


TestDataRecord = namedtuple(
    'TestDataRecord',
    'os,mode,controller,compute,cinder,ceph,network,networks_tagging,'
    'cinder_lvm,ceph_volumes,ceph_images,savanna,murano')


class TestParamsList:

    def __init__(self, file_path=None):
        self.file_path = \
            file_path or \
            os.path.dirname(os.path.abspath(__file__)) + '/testdata.csv'
        self.test_data = list()
        self.test_params = list()
        with open(self.file_path, 'rb') as csvfile:
            r = csv.reader(csvfile)
            self.test_data = map(TestDataRecord._make, r)
            # remove header
            self.test_data.pop(0)

            for td in self.test_data:
                obj = dict()
                obj['env'] = self._env(td)
                obj['nodes'] = self._nodes(td)
                obj['interfaces'] = self._interfaces(td)
                obj['env_attributes'] = self._env_attributes(td)
                obj['network_conf'] = self._network_conf(td)
                self.test_params.append(obj)

    def _env(self, td):
        o = dict()
        o['name'] = "TEST_%s" % datetime.now()
        o['mode'] = td.mode
        o['release'] = td.os
        o['settings'] = NET[td.network]
        return o

    def _nodes(self, td):
        o = dict()

        def append_nodes(i, role):
            for j in range(i, i + int(getattr(td, role)), 1):
                o['slave-0%s' % (j + 1)] = [role]

        append_nodes(len(o), 'controller')
        append_nodes(len(o), 'compute')
        append_nodes(len(o), 'cinder')
        append_nodes(len(o), 'ceph')
        return o

    def _interfaces(self, td):
        return copy.deepcopy(NODE_INTERFACES)

    def _env_attributes(self, td):
        o = copy.deepcopy(ENV_ATTRIBUTES)
        # storage
        if td.cinder_lvm == 'y':
            o['editable']['storage']['volumes_lvm']['value'] = True
        if td.ceph_volumes == 'y':
            o['editable']['storage']['volumes_ceph']['value'] = True
        if td.ceph_images == 'y':
            o['editable']['storage']['images_ceph']['value'] = True
        # additional components
        if td.savanna == 'y':
            o['editable']['additional_components']['savanna']['value'] = True
        if td.murano == 'y':
            o['editable']['additional_components']['murano']['value'] = True
        return o


    def _network_conf(self, td):
        o = {'networks': []}
        if td.networks_tagging == 'n':
            if 'nova' in td.network:
                o.update(NOVA_NETWORKS_UNTAGGED)
            if 'neutron' in td.network:
                o.update(NEUTRON_NETWORK_UNTAGGED)
        if td.network == 'nova_vlan':
            o.update(NET_MANAGER_VLAN)
        return o

    def __iter__(self):
        return iter(self.test_params)
