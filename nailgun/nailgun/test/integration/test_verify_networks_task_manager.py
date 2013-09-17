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
from mock import patch

from nailgun.settings import settings

from nailgun.test.base import BaseIntegrationTest
from nailgun.test.base import fake_tasks
from nailgun.test.base import reverse


@patch('nailgun.rpc.receiver.NailgunReceiver._get_master_macs')
class TestVerifyNetworkTaskManagers(BaseIntegrationTest):

    def setUp(self):
        self.master_macs = [{'addr': 'bc:ae:c5:e0:f5:85'},
                            {'addr': 'ee:ae:c5:e0:f5:17'}]
        self.not_master_macs = [{'addr': 'ee:ae:ee:e0:f5:85'}]

        super(TestVerifyNetworkTaskManagers, self).setUp()

        meta1 = self.env.generate_interfaces_in_meta(1)
        mac1 = meta1['interfaces'][0]['mac']
        meta2 = self.env.generate_interfaces_in_meta(1)
        mac2 = meta2['interfaces'][0]['mac']
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": True, "meta": meta1, "mac": mac1},
                {"api": True, "meta": meta2, "mac": mac2},
            ]
        )

    def tearDown(self):
        self._wait_for_threads()
        super(TestVerifyNetworkTaskManagers, self).tearDown()

    @fake_tasks()
    def test_network_verify_task_managers_dhcp_on_master(self, macs_mock):
        macs_mock.return_value = self.master_macs

        task = self.env.launch_verify_networks()
        self.env.wait_ready(task, 30)

    @fake_tasks()
    def test_network_verify_compares_received_with_cached(self, macs_mock):
        macs_mock.return_value = self.master_macs

        resp = self.app.get(
            reverse(
                'NetworkConfigurationHandler',
                kwargs={'cluster_id': self.env.clusters[0].id}
            ),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        nets = json.loads(resp.body)

        nets['networks'][-1]["vlan_start"] = 500
        task = self.env.launch_verify_networks(nets)
        self.env.wait_ready(task, 30)

    @fake_tasks(fake_rpc=False)
    def test_network_verify_fails_if_admin_intersection(self,
                                                        mocked_rpc, macs_mock):
        macs_mock.return_value = self.master_macs

        resp = self.app.get(
            reverse(
                'NetworkConfigurationHandler',
                kwargs={'cluster_id': self.env.clusters[0].id}
            ),
            headers=self.default_headers
        )
        self.assertEquals(200, resp.status)
        nets = json.loads(resp.body)

        nets['networks'][-1]['cidr'] = settings.ADMIN_NETWORK['cidr']

        task = self.env.launch_verify_networks(nets)
        self.env.wait_error(task, 30)
        self.assertIn(
            task.message,
            "Intersection with admin "
            "network(s) '{0}' found".format(
                settings.ADMIN_NETWORK['cidr']
            )
        )
        self.assertEquals(mocked_rpc.called, False)
