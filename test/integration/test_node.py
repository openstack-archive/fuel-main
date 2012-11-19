import os
import logging
import time
import json
import pprint
import posixpath
from devops.helpers import wait, tcp_ping, http
from integration import ci
from integration.base import Base
from helpers import SSHClient, HTTPClient
from root import root

logging.basicConfig(
    format=':%(lineno)d: %(asctime)s %(message)s',
    level=logging.DEBUG
)

AGENT_PATH = root("bin", "agent")
COOKBOOKS_PATH = root("cooks", "cookbooks")
SAMPLE_PATH = root("scripts", "ci")
SAMPLE_REMOTE_PATH = "/home/ubuntu"
REMOTE_PYTHON = "/opt/nailgun/bin/python"


class StillPendingException(Exception):
    pass


class TestNode(Base):
    def __init__(self, *args, **kwargs):
        super(TestNode, self).__init__(*args, **kwargs)
        self.remote = SSHClient()
        self.client = HTTPClient(
            url="http://%s:8000" % self.get_admin_node_ip()
        )
        self.ssh_user = "root"
        self.ssh_passwd = "r00tme"
        self.admin_host = self.get_admin_node_ip()
        self.remote.connect_ssh(
            self.admin_host,
            self.ssh_user,
            self.ssh_passwd
        )

    def setUp(self):
        pass

    def test_release_upload(self):
        self._upload_sample_release()

    def test_http_returns_200(self):
        resp = self.client.get("/")
        self.assertEquals(200, resp.getcode())

    def test_create_empty_cluster(self):
        self._create_cluster(name='empty')

    def test_node_deploy(self):
        self._bootstrap_slave()

    def test_updating_nodes_in_cluster(self):
        cluster_id = self._create_cluster(name='empty')
        node = str(self._bootstrap_slave()['id'])
        self._update_nodes_in_cluster(cluster_id, [node])

    def test_provisioning(self):
        self._clean_clusters()
        self._basic_provisioning('provision', 'slave')

    def test_node_deletion(self):
        cluster_name = 'node_deletion'
        node_name = 'slave-delete'
        cluster_id = self._basic_provisioning(cluster_name, node_name)

        slave = ci.environment.node[node_name]
        node = self._get_slave_node_by_devops_node(slave)
        self.client.put("/api/nodes/%s/" % node['id'],
                        {'pending_deletion': True})
        task = self._launch_provisioning(cluster_id)
        self._task_wait(task, 'Node deletion')

        timer = time.time()
        timeout = 3 * 60
        while True:
            response = self.client.get("/api/nodes/")
            nodes = json.loads(response.read())
            for n in nodes:
                if (n['mac'] == node['mac'] and n['status'] == 'discover'):
                    return
            if (time.time() - timer) > timeout:
                raise Exception("Bootstrap boot timeout expired!")
            time.sleep(5)

    def _basic_provisioning(self, cluster_name, node_name):
        self._clean_clusters()
        cluster_id = self._create_cluster(name=cluster_name)
        slave_id = str(self._bootstrap_slave(node_name)['id'])
        self.client.put("/api/nodes/%s/" % slave_id,
                        {"role": "controller", "pending_addition": True})
        self._update_nodes_in_cluster(cluster_id, [slave_id])
        task = self._launch_provisioning(cluster_id)

        self._task_wait(task, 'Installation')
        node = json.loads(self.client.get(
            "/api/nodes/%s/" % slave_id
        ).read())
        ctrl_ssh = SSHClient()
        ctrl_ssh.connect_ssh(node['ip'], 'root', 'r00tme')
        ret = ctrl_ssh.execute('test -f /tmp/controller-file')['exit_status']
        self.assertEquals(ret, 0)
        return cluster_id

    def _launch_provisioning(self, cluster_id):
        logging.info(
            "Launching provisioning on cluster %d",
            cluster_id
        )
        changes = self.client.put(
            "/api/clusters/%d/changes/" % cluster_id
        )
        self.assertEquals(200, changes.getcode())
        return json.loads(changes.read())

    def _task_wait(self, task, task_desc, timeout=30 * 60):
        timer = time.time()
        ready = False
        task_id = task['id']
        logging.info("Waiting task %r ..." % task_desc)
        while not ready:
            task = json.loads(
                self.client.get("/api/tasks/%s" % task_id).read()
            )
            if task['status'] == 'ready':
                logging.info("Task %r complete" % task_desc)
                ready = True
            elif task['status'] == 'running':
                if (time.time() - timer) > timeout:
                    raise Exception("Task %r timeout expired!" % task_desc)
                time.sleep(30)
            else:
                raise Exception("%s failed!" % task_desc)

    def _upload_sample_release(self):
        def _get_release_id():
            releases = json.loads(
                self.client.get("/api/releases/").read()
            )
            for r in releases:
                logging.debug("Found release name: %s" % r["name"])
                if r["name"] == "OpenStack Essex Release":
                    logging.debug("Sample release id: %s" % r["id"])
                    return r["id"]

        release_id = _get_release_id()
        if not release_id:
            raise "Not implemented uploading of release"
        if not release_id:
            raise Exception("Could not get release id.")
        return release_id

    def _create_cluster(self, name='default', release_id=None):
        if not release_id:
            release_id = self._upload_sample_release()

        def _get_cluster_id(name):
            clusters = json.loads(
                self.client.get("/api/clusters/").read()
            )
            for cl in clusters:
                logging.debug("Found cluster name: %s" % cl["name"])
                if cl["name"] == name:
                    logging.debug("Cluster id: %s" % cl["id"])
                    return cl["id"]

        cluster_id = _get_cluster_id(name)
        if not cluster_id:
            resp = self.client.post(
                "/api/clusters",
                data={"name": name, "release": str(release_id)}
            )
            self.assertEquals(201, resp.getcode())
            cluster_id = _get_cluster_id(name)
        if not cluster_id:
            raise Exception("Could not get cluster '%s'" % name)
        return cluster_id

    def _clean_clusters(self):
        clusters = json.loads(self.client.get(
            "/api/clusters/"
        ).read())
        for cluster in clusters:
            resp = self.client.put(
                "/api/clusters/%s" % cluster["id"],
                data={"nodes": []}
            ).read()

    def _update_nodes_in_cluster(self, cluster_id, nodes):
        resp = self.client.put(
            "/api/clusters/%s" % cluster_id,
            data={"nodes": nodes})
        self.assertEquals(200, resp.getcode())
        cluster = json.loads(self.client.get(
            "/api/clusters/%s" % cluster_id).read())
        nodes_in_cluster = [str(n['id']) for n in cluster['nodes']]
        self.assertEquals(nodes, nodes_in_cluster)

    def _get_slave_node_by_devops_node(self, node):
        response = self.client.get("/api/nodes/")
        nodes = json.loads(response.read())
        logging.debug("get_slave_node_by_devops_node: nodes at nailgun: %r" %
                      str(nodes))

        for n in nodes:
            for i in node.interfaces:
                logging.debug("get_slave_node_by_devops_node: \
node.interfaces[n].mac_address: %r" % str(i.mac_address))
                if n['mac'].capitalize() == i.mac_address.capitalize():
                    return n
        return None

    def _bootstrap_slave(self, node_name='slave'):
        """This function returns nailgun node descpription by devops name.
        """
        try:
            self.get_slave_id()
        except:
            pass
        timer = time.time()
        timeout = 600

        slave = ci.environment.node[node_name]
        logging.info("Starting slave node %r" % node_name)
        slave.start()

        while True:
            node = self._get_slave_node_by_devops_node(slave)
            if node is not None:
                logging.debug("Node %r found" % node_name)
                break
            else:
                logging.debug("Node %r not found" % node_name)
                if (time.time() - timer) > timeout:
                    raise Exception("Slave node agent failed to execute!")
                time.sleep(15)
                logging.info("Waiting for slave agent to run...")
        return node
