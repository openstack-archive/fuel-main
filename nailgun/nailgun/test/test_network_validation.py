# -*- coding: utf-8 -*-

import json

from nailgun.api.models import Network, NetworkGroup
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.settings import settings


class TestHandlers(BaseHandlers):

    def test_network_checking(self):
        cluster = self.create_cluster_api()
        node = self.create_default_node(cluster_id=cluster['id'],
                                        role="controller",
                                        pending_addition=True)

        nets = self.generate_ui_networks(cluster["id"])
        resp = self.app.put(
            reverse('ClusterSaveNetworksHandler',
                    kwargs={'cluster_id': cluster['id']}),
            json.dumps(nets),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)
        task = json.loads(resp.body)
        self.assertEquals(task['status'], 'ready')
        self.assertEquals(task['progress'], 100)
        self.assertEquals(task['name'], 'check_networks')

    def test_network_checking_fails_if_admin_intersection(self):
        cluster = self.create_cluster_api()
        node = self.create_default_node(cluster_id=cluster['id'],
                                        role="controller",
                                        pending_addition=True)
        nets = self.generate_ui_networks(cluster["id"])
        nets[-1]["cidr"] = settings.NET_EXCLUDE[0]
        resp = self.app.put(
            reverse('ClusterSaveNetworksHandler',
                    kwargs={'cluster_id': cluster['id']}),
            json.dumps(nets),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 400)
        self.assertEquals(
            resp.body,
            "Intersection with admin "
            "network(s) '{0}' found".format(
                settings.NET_EXCLUDE
            )
        )

    def test_network_checking_fails_if_admin_intersection(self):
        cluster = self.create_cluster_api()
        node = self.create_default_node(cluster_id=cluster['id'],
                                        role="controller",
                                        pending_addition=True)
        nets = self.generate_ui_networks(cluster["id"])
        nets[-1]["cidr"] = settings.NET_EXCLUDE[0]
        resp = self.app.put(
            reverse('ClusterSaveNetworksHandler',
                    kwargs={'cluster_id': cluster['id']}),
            json.dumps(nets),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp.status, 400)
        self.assertEquals(
            resp.body,
            "Intersection with admin "
            "network(s) '{0}' found".format(
                settings.NET_EXCLUDE
            )
        )
