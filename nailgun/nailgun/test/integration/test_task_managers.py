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
import time

from nailgun.settings import settings

from nailgun.api.models import Cluster
from nailgun.api.models import Node
from nailgun.api.models import Notification
from nailgun.api.models import Task
from nailgun.errors import errors
import nailgun.rpc as rpc
from nailgun.task.manager import DeploymentTaskManager
from nailgun.test.base import BaseIntegrationTest
from nailgun.test.base import fake_tasks
from nailgun.test.base import reverse


class TestTaskManagers(BaseIntegrationTest):

    def tearDown(self):
        self._wait_for_threads()
        super(TestTaskManagers, self).tearDown()

    @fake_tasks()
    def test_deployment_task_managers(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"pending_addition": True},
                {"pending_deletion": True},
            ]
        )
        supertask = self.env.launch_deployment()
        self.assertEquals(supertask.name, 'deploy')
        self.assertIn(supertask.status, ('running', 'ready'))
        # we have three subtasks here
        # deletion
        # provision
        # deployment
        self.assertEquals(len(supertask.subtasks), 3)

        self.env.wait_for_nodes_status([self.env.nodes[0]], 'provisioning')
        self.env.wait_ready(
            supertask,
            60,
            u"Successfully removed 1 node(s). No errors occurred; "
            "Deployment of environment '{0}' is done".format(
                self.env.clusters[0].name
            )
        )
        self.env.refresh_nodes()
        for n in filter(
            lambda n: n.cluster_id == self.env.clusters[0].id,
            self.env.nodes
        ):
            self.assertEquals(n.status, 'ready')
            self.assertEquals(n.progress, 100)

    @fake_tasks()
    def test_do_not_redeploy_nodes_in_ready_status(self):
        self.env.create(nodes_kwargs=[
            {"pending_addition": True},
            {"pending_addition": True}])
        cluster_db = self.env.clusters[0]
        # Generate ips, fqdns
        cluster_db.prepare_for_deployment()
        # First node with status ready
        # should not be readeployed
        self.env.nodes[0].status = 'ready'
        self.db.commit()

        cluster_db.clear_pending_changes()

        supertask = self.env.launch_deployment()
        self.assertEquals(supertask.name, 'deploy')
        self.assertIn(supertask.status, ('running', 'ready'))

        self.assertEquals(self.env.nodes[0].status, 'ready')
        self.env.wait_for_nodes_status([self.env.nodes[1]], 'provisioning')
        self.env.wait_ready(supertask)

        self.env.refresh_nodes()

        self.assertEquals(self.env.nodes[1].status, 'ready')
        self.assertEquals(self.env.nodes[1].progress, 100)

    @fake_tasks()
    def test_deployment_fails_if_node_offline(self):
        cluster = self.env.create_cluster(api=True)
        self.env.create_node(cluster_id=cluster['id'],
                             roles=["controller"],
                             pending_addition=True)
        self.env.create_node(cluster_id=cluster['id'],
                             roles=["compute"],
                             online=False,
                             name="Offline node",
                             pending_addition=True)
        self.env.create_node(cluster_id=cluster['id'],
                             roles=["compute"],
                             pending_addition=True)
        supertask = self.env.launch_deployment()
        self.env.wait_error(
            supertask,
            60,
            u"Deployment has failed. Check these nodes:\n"
            "'Offline node'"
        )

    @fake_tasks()
    def test_redeployment_works(self):
        self.env.create(
            cluster_kwargs={"mode": "ha_compact"},
            nodes_kwargs=[
                {"pending_addition": True},
                {"pending_addition": True},
                {"pending_addition": True},
                {"roles": ["compute"], "pending_addition": True}
            ]
        )
        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask, 60)
        self.env.refresh_nodes()

        self.env.create_node(
            cluster_id=self.env.clusters[0].id,
            roles=["controller"],
            pending_addition=True
        )

        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask, 60)
        self.env.refresh_nodes()
        for n in self.env.nodes:
            self.assertEquals(n.status, 'ready')
            self.assertEquals(n.progress, 100)

    @fake_tasks()
    def test_redeployment_error_nodes(self):
        self.env.create(
            cluster_kwargs={"mode": "ha_compact"},
            nodes_kwargs=[
                {
                    "pending_addition": True,
                    "status": "error",
                    "error_type": "provision",
                    "error_msg": "Test Error"
                },
                {"pending_addition": True},
                {"pending_addition": True},
                {"roles": ["compute"], "pending_addition": True}
            ]
        )
        supertask = self.env.launch_deployment()
        self.env.wait_error(supertask, 60)
        self.env.refresh_nodes()
        self.assertEquals(self.env.nodes[0].status, 'error')
        self.assertEquals(self.env.nodes[0].needs_reprovision, True)
        self.assertEquals(self.env.nodes[1].status, 'provisioned')
        notif_node = self.db.query(Notification).filter_by(
            topic="error",
            message=u"Failed to deploy node '{0}': {1}".format(
                self.env.nodes[0].name,
                self.env.nodes[0].error_msg
            )
        ).first()
        self.assertIsNotNone(notif_node)
        notif_deploy = self.db.query(Notification).filter_by(
            topic="error",
            message=u"Deployment has failed. "
            "Check these nodes:\n'{0}'".format(
                self.env.nodes[0].name
            )
        ).first()
        self.assertIsNotNone(notif_deploy)
        all_notif = self.db.query(Notification).all()
        self.assertEqual(len(all_notif), 2)
        supertask = self.env.launch_deployment()
        self.env.wait_error(supertask, 60)

    @fake_tasks()
    def test_network_verify_task_managers(self):
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

        task = self.env.launch_verify_networks()
        self.env.wait_ready(task, 30)

    @fake_tasks()
    def test_network_verify_compares_received_with_cached(self):
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
    def test_network_verify_fails_if_admin_intersection(self, mocked_rpc):
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

    def test_deletion_empty_cluster_task_manager(self):
        cluster = self.env.create_cluster(api=True)
        resp = self.app.delete(
            reverse(
                'ClusterHandler',
                kwargs={'cluster_id': self.env.clusters[0].id}),
            headers=self.default_headers
        )
        self.assertEquals(202, resp.status)

        timer = time.time()
        timeout = 15
        clstr = self.db.query(Cluster).get(self.env.clusters[0].id)
        while clstr:
            time.sleep(1)
            try:
                self.db.refresh(clstr)
            except Exception:
                break
            if time.time() - timer > timeout:
                raise Exception("Cluster deletion seems to be hanged")

        notification = self.db.query(Notification)\
            .filter(Notification.topic == "done")\
            .filter(Notification.message == "Environment '%s' and all its "
                    "nodes are deleted" % cluster["name"]).first()
        self.assertIsNotNone(notification)

        tasks = self.db.query(Task).all()
        self.assertEqual(tasks, [])

    @fake_tasks()
    def test_deletion_cluster_task_manager(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"status": "ready", "progress": 100},
                {"roles": ["compute"], "status": "ready", "progress": 100},
                {"roles": ["compute"], "pending_addition": True},
            ]
        )
        cluster_id = self.env.clusters[0].id
        cluster_name = self.env.clusters[0].name
        resp = self.app.delete(
            reverse(
                'ClusterHandler',
                kwargs={'cluster_id': cluster_id}),
            headers=self.default_headers
        )
        self.assertEquals(202, resp.status)

        timer = time.time()
        timeout = 15
        clstr = self.db.query(Cluster).get(cluster_id)
        while clstr:
            time.sleep(1)
            try:
                self.db.refresh(clstr)
            except Exception:
                break
            if time.time() - timer > timeout:
                raise Exception("Cluster deletion seems to be hanged")

        notification = self.db.query(Notification)\
            .filter(Notification.topic == "done")\
            .filter(Notification.message == "Environment '%s' and all its "
                    "nodes are deleted" % cluster_name).first()
        self.assertIsNotNone(notification)

        tasks = self.db.query(Task).all()
        self.assertEqual(tasks, [])

    @fake_tasks()
    def test_deletion_during_deployment(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"status": "ready", "pending_addition": True},
            ]
        )
        cluster_id = self.env.clusters[0].id
        resp = self.app.put(
            reverse(
                'ClusterChangesHandler',
                kwargs={'cluster_id': cluster_id}),
            headers=self.default_headers
        )
        deploy_uuid = json.loads(resp.body)['uuid']
        resp = self.app.delete(
            reverse(
                'ClusterHandler',
                kwargs={'cluster_id': cluster_id}),
            headers=self.default_headers
        )
        timeout = 120
        timer = time.time()
        while True:
            task_deploy = self.db.query(Task).filter_by(
                uuid=deploy_uuid
            ).first()
            task_delete = self.db.query(Task).filter_by(
                cluster_id=cluster_id,
                name="cluster_deletion"
            ).first()
            if not task_delete:
                break
            self.db.expire(task_deploy)
            self.db.expire(task_delete)
            if (time.time() - timer) > timeout:
                break
            time.sleep(0.24)

        cluster_db = self.db.query(Cluster).get(cluster_id)
        self.assertIsNone(cluster_db)

    @fake_tasks()
    def test_deletion_cluster_ha_3x3(self):
        self.env.create(
            cluster_kwargs={
                "api": True,
                "mode": "ha_compact"
            },
            nodes_kwargs=[
                {"roles": ["controller"], "pending_addition": True},
                {"roles": ["compute"], "pending_addition": True}
            ] * 3
        )
        cluster_id = self.env.clusters[0].id
        cluster_name = self.env.clusters[0].name
        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask)

        resp = self.app.delete(
            reverse(
                'ClusterHandler',
                kwargs={'cluster_id': cluster_id}),
            headers=self.default_headers
        )
        self.assertEquals(202, resp.status)

        timer = time.time()
        timeout = 15
        clstr = self.db.query(Cluster).get(cluster_id)
        while clstr:
            time.sleep(1)
            try:
                self.db.refresh(clstr)
            except Exception:
                break
            if time.time() - timer > timeout:
                raise Exception("Cluster deletion seems to be hanged")

        notification = self.db.query(Notification)\
            .filter(Notification.topic == "done")\
            .filter(Notification.message == "Environment '%s' and all its "
                    "nodes are deleted" % cluster_name).first()
        self.assertIsNotNone(notification)

        tasks = self.db.query(Task).all()
        self.assertEqual(tasks, [])

    @fake_tasks()
    def test_node_fqdn_is_assigned(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"pending_addition": True},
                {"pending_addition": True}
            ]
        )
        self.env.launch_deployment()
        self.env.refresh_nodes()
        for node in self.env.nodes:
            fqdn = "node-%s.%s" % (node.id, settings.DNS_DOMAIN)
            self.assertEquals(fqdn, node.fqdn)

    @fake_tasks()
    def test_no_node_no_cry(self):
        cluster = self.env.create_cluster(api=True)
        rcvr = rpc.receiver.NailgunReceiver
        manager = DeploymentTaskManager(cluster["id"])
        rcvr.deploy_resp(nodes=[
            {'uid': 666, 'id': 666, 'status': 'discover'}
        ], uuid='no_freaking_way')  # and wrong task also
        self.assertRaises(errors.WrongNodeStatus, manager.execute)

    @fake_tasks()
    def test_no_changes_no_cry(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"status": "ready"}
            ]
        )
        cluster_db = self.env.clusters[0]
        cluster_db.clear_pending_changes()
        manager = DeploymentTaskManager(cluster_db.id)
        self.assertRaises(errors.WrongNodeStatus, manager.execute)

    @fake_tasks()
    def test_deletion_offline_node(self):
        cluster = self.env.create_cluster()
        self.env.create_node(
            cluster_id=cluster['id'],
            online=False,
            pending_deletion=True)

        self.env.create_node(
            cluster_id=cluster['id'],
            status='ready')

        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask, timeout=5)
        self.assertEquals(self.env.db.query(Node).count(), 1)

    @fake_tasks()
    def test_deletion_three_offline_nodes_and_one_online(self):
        cluster = self.env.create_cluster()
        for _ in range(3):
            self.env.create_node(
                cluster_id=cluster['id'],
                online=False,
                pending_deletion=True)

        self.env.create_node(
            cluster_id=cluster['id'],
            online=True,
            pending_deletion=True)

        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask, timeout=5)

        self.assertEquals(self.env.db.query(Node).count(), 1)
        node = self.db.query(Node).first()
        self.assertEquals(node.status, 'discover')
        self.assertEquals(node.cluster_id, None)

    @fake_tasks()
    def test_deletion_offline_node_when_cluster_has_only_one_node(self):
        cluster = self.env.create_cluster()
        self.env.clusters[0].clear_pending_changes()
        self.env.create_node(
            cluster_id=cluster['id'],
            online=False,
            pending_deletion=True,
            pending_addition=False,
            status='ready')

        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask, timeout=5)
        self.assertEquals(self.env.db.query(Node).count(), 0)
