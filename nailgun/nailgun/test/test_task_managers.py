# -*- coding: utf-8 -*-
import json
import time

from mock import patch

from nailgun.settings import settings

import nailgun
import nailgun.rpc as rpc
from nailgun.task.manager import DeploymentTaskManager
from nailgun.task.fake import FAKE_THREADS
from nailgun.errors import errors
from nailgun.test.base import BaseHandlers
from nailgun.test.base import reverse
from nailgun.test.base import fake_tasks
from nailgun.api.models import Cluster, Attributes, Task, Notification, Node


class TestTaskManagers(BaseHandlers):

    def tearDown(self):
        self._wait_for_threads()

    @fake_tasks()
    def test_deployment_task_managers(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"pending_addition": True},
                {"status": "ready", "pending_addition": True},
                {"pending_deletion": True},
            ]
        )
        supertask = self.env.launch_deployment()
        self.assertEquals(supertask.name, 'deploy')
        self.assertIn(supertask.status, ('running', 'ready'))
        self.assertEquals(len(supertask.subtasks), 2)

        timer = time.time()
        timeout = 10
        while True:
            self.env.refresh_nodes()
            if self.env.nodes[0].status in \
                    ('provisioning', 'provisioned') and \
                    self.env.nodes[1].status == 'provisioned':
                break
            if time.time() - timer > timeout:
                raise Exception("Something wrong with the statuses")
            time.sleep(1)

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
    def test_deployment_fails_if_node_offline(self):
        cluster = self.env.create_cluster(api=True)
        node1 = self.env.create_node(cluster_id=cluster['id'],
                                     role="controller",
                                     pending_addition=True)
        node2 = self.env.create_node(cluster_id=cluster['id'],
                                     role="compute",
                                     online=False,
                                     name="Offline node",
                                     pending_addition=True)
        node3 = self.env.create_node(cluster_id=cluster['id'],
                                     role="compute",
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
            cluster_kwargs={"mode": "ha"},
            nodes_kwargs=[
                {"pending_addition": True},
                {"role": "compute", "pending_addition": True}
            ]
        )
        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask, 60)
        self.env.refresh_nodes()

        node3 = self.env.create_node(
            cluster_id=self.env.clusters[0].id,
            role="controller",
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
            cluster_kwargs={"mode": "ha"},
            nodes_kwargs=[
                {
                    "pending_addition": True,
                    "status": "error",
                    "error_type": "provision",
                    "error_msg": "Test Error"
                },
                {"role": "compute", "pending_addition": True}
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
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False},
            ]
        )

        task = self.env.launch_verify_networks()
        self.env.wait_ready(task, 30)

    @fake_tasks()
    def test_network_verify_compares_received_with_cached(self):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False},
            ]
        )
        nets = self.env.generate_ui_networks(
            self.env.clusters[0].id
        )
        nets['networks'][-1]["vlan_start"] = 500
        task = self.env.launch_verify_networks(nets)
        self.env.wait_ready(task, 30)

    @fake_tasks(fake_rpc=False)
    def test_network_verify_fails_if_admin_intersection(self, mocked_rpc):
        self.env.create(
            cluster_kwargs={},
            nodes_kwargs=[
                {"api": False},
                {"api": False},
            ]
        )
        nets = self.env.generate_ui_networks(
            self.env.clusters[0].id
        )
        nets['networks'][-1]['cidr'] = settings.NET_EXCLUDE[0]

        task = self.env.launch_verify_networks(nets)
        self.env.wait_error(task, 30)
        self.assertIn(
            task.message,
            "Intersection with admin "
            "network(s) '{0}' found".format(
                settings.NET_EXCLUDE
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
            except:
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
                {"role": "compute", "status": "ready", "progress": 100},
                {"role": "compute", "pending_addition": True},
            ]
        )
        cluster_id = self.env.clusters[0].id
        cluster_name = self.env.clusters[0].name
        nodes_ids = [n.id for n in self.env.nodes]
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
            except:
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
                {"status": "ready",  "pending_addition": True},
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
                "mode": "ha"
            },
            nodes_kwargs=[
                {"role": "controller", "pending_addition": True},
                {"role": "compute", "pending_addition": True}
            ] * 3
        )
        cluster_id = self.env.clusters[0].id
        cluster_name = self.env.clusters[0].name
        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask)

        nodes_ids = [n.id for n in self.env.nodes]
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
            except:
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
            fqdn = "slave-%s.%s" % (node.id, settings.DNS_DOMAIN)
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
