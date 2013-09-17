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

import json

from nailgun.test.base import BaseIntegrationTest
from nailgun.test.base import reverse


class TestHandlers(BaseIntegrationTest):

    def test_put_handler_with_one_node(self):
        cluster = self.env.create_cluster(api=True)
        mac = '123'
        meta = {'interfaces': [
            {'name': 'eth0', 'mac': mac},
            {'name': 'eth1', 'mac': '654'},
        ]}
        node = self.env.create_node(api=True, meta=meta, mac=mac,
                                    cluster_id=cluster['id'])
        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        a_nets = filter(lambda nic: nic['mac'] == mac,
                        response)[0]['assigned_networks']
        for resp_nic in response:
            if resp_nic['mac'] == mac:
                resp_nic['assigned_networks'] = []
            else:
                resp_nic['assigned_networks'] = a_nets
        node_json = {'id': node['id'], 'interfaces': response}
        resp = self.app.put(
            reverse('NodeCollectionNICsHandler'),
            json.dumps([node_json]),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        new_response = json.loads(resp.body)
        self.assertEquals(new_response, [node_json])
