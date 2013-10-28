from collections import namedtuple
import copy
import csv
import os
from datetime import datetime


NODE_INTERFACES = {
    'nova_flat': {
        'eth0': [],
        'eth1': ["public", "floating"],
        'eth2': ["management"],
        'eth3': ["fixed", "storage"]
    },
    'nova_vlan': {
        'eth0': [],
        'eth1': ["public", "floating"],
        'eth2': ["management"],
        'eth3': ["fixed", "storage"]
    },
    'neutron_gre': {
        'eth0': [],
        'eth1': ["public"],
        'eth2': ["management"],
        'eth3': ["storage"]
    },
    'neutron_vlan': {
        'eth0': [],
        'eth1': ["public", "management"],
        'eth2': ["private"],
        'eth3': ["storage"]
    }
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
                test_params_obj = TestParams(td)
                obj['env'] = test_params_obj.env()
                obj['nodes'] = test_params_obj.nodes()
                obj['interfaces'] = test_params_obj.interfaces()
                obj['env_attributes'] = test_params_obj.env_attributes()
                obj['network_conf'] = test_params_obj.network_conf()
                self.test_params.append(obj)

    def __iter__(self):
        return iter(self.test_params)


class TestParams:

    def __init__(self, testdata):
        self.testdata = testdata

    def env(self):
        o = dict()
        o['name'] = "TEST_%s" % datetime.now()
        o['mode'] = self.testdata.mode
        o['release'] = self.testdata.os
        o['settings'] = NET[self.testdata.network]
        return o

    def nodes(self):
        o = dict()

        def append_nodes(i, csv_name, role=None):
            role = role or csv_name
            for j in range(i, i + int(getattr(self.testdata, csv_name)), 1):
                o['slave-0%s' % (j + 1)] = [role]

        append_nodes(len(o), 'controller')
        append_nodes(len(o), 'compute')
        append_nodes(len(o), 'cinder')
        append_nodes(len(o), 'ceph', 'ceph-osd')
        return o

    def interfaces(self):
        return copy.deepcopy(NODE_INTERFACES[self.testdata.network])

    def env_attributes(self):
        o = copy.deepcopy(ENV_ATTRIBUTES)
        # storage
        if self.testdata.cinder_lvm == 'y':
            o['editable']['storage']['volumes_lvm']['value'] = True
        if self.testdata.ceph_volumes == 'y':
            o['editable']['storage']['volumes_ceph']['value'] = True
        if self.testdata.ceph_images == 'y':
            o['editable']['storage']['images_ceph']['value'] = True
        # additional components
        if self.testdata.savanna == 'y':
            o['editable']['additional_components']['savanna']['value'] = True
        if self.testdata.murano == 'y':
            o['editable']['additional_components']['murano']['value'] = True
        return o


    def network_conf(self):
        o = {'networks': []}
        if self.testdata.networks_tagging == 'n':
            if 'nova' in self.testdata.network:
                o.update(NOVA_NETWORKS_UNTAGGED)
            if 'neutron' in self.testdata.network:
                o.update(NEUTRON_NETWORK_UNTAGGED)
        if self.testdata.network == 'nova_vlan':
            o.update(NET_MANAGER_VLAN)
        return o
