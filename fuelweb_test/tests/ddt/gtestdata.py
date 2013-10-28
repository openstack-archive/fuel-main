import copy
import os
from datetime import datetime
import json
from gdata.spreadsheet import text_db


GOOGLE_LOGIN = os.environ.get('GOOGLE_LOGIN')
GOOGLE_PASSWORD = os.environ.get('GOOGLE_PASSWORD')
GOOGLE_SPREEDSHEET = os.environ.get('GOOGLE_SPREEDSHEET')

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


class TestParamsList:

    def __init__(self):
        self.test_params = list()

        def to_dict(records, key_field):
            r = dict()
            for record in records:
                r[record.content[key_field]] = record.content
            return r

        # connect to google spreadsheet and get tables
        self.gclient = text_db.DatabaseClient(GOOGLE_LOGIN, GOOGLE_PASSWORD)
        self.gspreadsheet = \
            self.gclient.GetDatabases(spreadsheet_key=GOOGLE_SPREEDSHEET)[0]
        self.gtbl_main = self.gspreadsheet.GetTables(name='main')[0]
        self.gtbl_networks = self.gspreadsheet.GetTables(name='networks')[0]
        self.gtbl_node_networks = \
            self.gspreadsheet.GetTables(name='node networks')[0]

        # get table content, convert some tables into dictionaries
        mains = self.gtbl_main.FindRecords('id != None')
        networks = to_dict(self.gtbl_networks.FindRecords('id != None'), 'id')
        node_networks = \
            to_dict(self.gtbl_node_networks.FindRecords('id != None'), 'id')

        # replace IDs with objects. Build test_params list
        for main in mains:
            data = copy.deepcopy(main.content)
            data['network'] = networks[data['network']]
            data['nodenetworks'] = node_networks[data['nodenetworks']]

            self.test_params.append(TestParams(data))

    def __iter__(self):
        return iter(self.test_params)


class TestParams:
    """Store data for one test run. Provides information for configuring
    environment.
    """

    def __init__(self, data):
        self.data = data

        self._environment = None
        self._nodes = None
        self._interfaces = None
        self._settings = None
        self._networks = None

    @property
    def environment(self):
        if self._environment is None:
            self._environment = {
                'name': "TEST_%s" % datetime.now(),
                'mode': self.data['mode'],
                'release': self.data['os'],
                'settings': {}
            }
            if 'neutron' == self.data['network']['netprovider']:
                self._environment['settings'] = {
                    'net_provider': self.data['network']['netprovider'],
                    'net_segment_type': self.data['network']['netsegmenttype']
                }
        return self._environment

    @property
    def nodes(self):
        if self._nodes is None:
            self._nodes = dict()
            for i in range(1, 10):
                node_name = 'slave-0%s' % i
                if self.data[node_name] is not None:
                    self._nodes[node_name] = self.data[node_name].split(',')
        return self._nodes

    @property
    def interfaces(self):
        if self._interfaces is None:
            self._interfaces = dict()
            for i in range(0, 4):
                interface_name = 'eth%s' % i
                nn = self.data['nodenetworks'][interface_name]
                self._interfaces[interface_name] = \
                    nn.split(',') if nn is not None else []
        return self._interfaces

    @property
    def settings(self):
        if self._settings is None:
            self._settings = {
                'editable': {
                    'storage': {
                        'volumes_lvm': {
                            'value': self.data['volumeslvm'] == 'TRUE'},
                        'images_ceph': {
                            'value': self.data['volumesceph'] == 'TRUE'},
                        'volumes_ceph': {
                            'value': self.data['imagesceph'] == 'TRUE'},
                        'objects_ceph': {
                            'value': self.data['radosgw'] == 'TRUE'}
                    },
                    'additional_components': {
                        'savanna': {
                            'value': self.data['savanna'] == 'TRUE'},
                        'murano': {
                            'value': self.data['murano'] == 'TRUE'}
                    }
                }
            }
        return self._settings

    @property
    def networks(self):
        if self._networks is None:
            self._networks = {'networks': []}
            if self.data['nettagging'] == 'FALSE':
                if 'nova_network' in self.data['network']['netprovider']:
                    self._networks.update(NOVA_NETWORKS_UNTAGGED)
                if 'neutron' in self.data['network']['netprovider']:
                    self._networks.update(NEUTRON_NETWORK_UNTAGGED)
            if self.data['network']['netmanager'] is not None:
                self._networks['net_manager'] = \
                    self.data['network']['netmanager']
        return self._networks

    def __str__(self):
        return json.dumps({
            'environment': self.environment,
            'nodes': self.nodes,
            'interfaces': self.interfaces,
            'settings': self.settings,
            'networks': self.networks
        }, indent=2)




