#    Copyright 2014 Mirantis, Inc.
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

import copy
import os
from datetime import datetime
from gdata.spreadsheet import text_db

GOOGLE_LOGIN = os.environ.get('GOOGLE_LOGIN')
GOOGLE_PASSWORD = os.environ.get('GOOGLE_PASSWORD')
GOOGLE_SPREEDSHEET = os.environ.get('GOOGLE_SPREEDSHEET')


class TestParamsList:

    def __init__(self):
        self.test_params = list()

        to_dict = lambda records, key_field: \
            {record.content[key_field]: record.content for record in records}

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

        self._settings = None
        self._nodes = None
        self._interfaces = None

    @property
    def name(self):
        return "TEST_%s" % datetime.now()

    @property
    def mode(self):
        return self.data['mode']

    @property
    def release(self):
        return self.data['os']

    @property
    def settings(self):
        parse_bool = lambda v: v == 'TRUE'
        if self._settings is None:
            self._settings = {
                'volumes_lvm': parse_bool(self.data['volumeslvm']),
                'images_ceph': parse_bool(self.data['volumesceph']),
                'volumes_ceph': parse_bool(self.data['imagesceph']),
                'objects_ceph': parse_bool(self.data['radosgw']),
                'savanna': parse_bool(self.data['savanna']),
                'murano': parse_bool(self.data['murano'])
            }
            if 'neutron' == self.data['network']['netprovider']:
                self._settings.update({
                    'net_provider': self.data['network']['netprovider'],
                    'net_segment_type': self.data['network']['netsegmenttype']
                })
            if 'nova_network' == self.data['network']['netprovider']:
                self._settings.update({
                    'net_manager': self.data['network']['netmanager']
                })
        return self._settings

    @property
    def nodes(self):
        if self._nodes is None:
            self._nodes = {}
            for role in ['controller', 'compute', 'cinder', 'ceph-osd']:
                name = lambda num: 'slave-0%s' % num
                amount = int(self.data[role] or 0)
                self._nodes.update(
                    {name(i + 1): [role]
                     for i in range(len(self._nodes),
                                    len(self._nodes) + amount)})
        return self._nodes

    @property
    def interfaces(self):
        if self._interfaces is None:
            self._interfaces = {'eth%s' % i: [] for i in range(0, 4)}
            for name in self._interfaces.keys():
                nn = self.data['nodenetworks'][name]
                if nn is not None:
                    self._interfaces[name] = nn.split(',')
        return self._interfaces
