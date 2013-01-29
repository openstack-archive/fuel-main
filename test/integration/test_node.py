import os
import sys
import traceback
import logging
import time
import json
import pprint
import posixpath
import re
import subprocess
from time import sleep

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


def snapshot_errors(func):
    """ Decorator to snapshot nodes when error occured in test.
    """
    def decorator(*args, **kwagrs):
        ss_name = 'error-%d' % int(time.time())
        desc = "Failed in method '%s'" % func.__name__
        try:
            func(*args, **kwagrs)
        except Exception, e:
            exc = list(sys.exc_info())
            exc[2] = exc[2].tb_next
            logging.warn('Some raise occered in method "%s"' % func.__name__)
            logging.warn(''.join(traceback.format_exception(*exc)))
            for node in ci.environment.nodes:
                logging.info("Creating snapshot '%s' for node %s" %
                             (ss_name, node.name))
                node.save_snapshot(ss_name, desc)
            raise Exception(e), None, sys.exc_info()[2].tb_next
    newfunc = decorator
    newfunc.__dict__ = func.__dict__
    newfunc.__doc__ = func.__doc__
    newfunc.__module__ = func.__module__
    newfunc.__name__ = func.__name__
    return newfunc


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

    @snapshot_errors
    def test_node_deploy(self):
        self._revert_nodes()
        self._bootstrap_nodes(['slave1'])

    @snapshot_errors
    def test_updating_nodes_in_cluster(self):
        self._revert_nodes()
        cluster_id = self._create_cluster(name='empty')
        nodes = self._bootstrap_nodes(['slave1'])
        self._update_nodes_in_cluster(cluster_id, nodes)

    @snapshot_errors
    def test_one_node_provisioning(self):
        self._revert_nodes()
        self._clean_clusters()
        self._basic_provisioning('provision', {'controller': ['slave1']})

    @snapshot_errors
    def test_two_nodes_provisioning(self):
        self._revert_nodes()
        cluster_name = 'two_nodes'
        nodes = {'controller': ['slave1'], 'compute': ['slave2']}
        self._basic_provisioning(cluster_name, nodes)
        slave = ci.environment.node['slave1']
        node = self._get_slave_node_by_devops_node(slave)
        wait(lambda: self._check_cluster_status(node['ip']), timeout=300)

    @snapshot_errors
    def test_ha_cluster(self):
        self._revert_nodes()
        cluster_name = 'ha_cluster'
        nodes = {
            'controller': ['slave1', 'slave2', 'slave3'],
            'compute': ['slave4', 'slave5']
        }
        self._basic_provisioning(cluster_name, nodes)
        slave = ci.environment.node['slave1']
        node = self._get_slave_node_by_devops_node(slave)
        wait(lambda: self._check_cluster_status(node['ip']), timeout=300)

    @snapshot_errors
    def test_network_config(self):
        self._revert_nodes()
        self._clean_clusters()
        self._basic_provisioning('network_config', {'controller': ['slave1']})

        slave = ci.environment.node['slave1']
        node = self._get_slave_node_by_devops_node(slave)
        ctrl_ssh = SSHClient()
        ctrl_ssh.connect_ssh(node['ip'], 'root', 'r00tme')
        ifaces_fail = False
        for iface in node['network_data']:
            try:
                ifname = "%s.%s@%s" % (
                    iface['dev'], iface['vlan'], iface['dev']
                )
                ifname_short = "%s.%s" % (iface['dev'], iface['vlan'])
            except KeyError:
                ifname = iface['dev']
            iface_data = ''.join(
                ctrl_ssh.execute(
                    '/sbin/ip addr show dev %s' % ifname_short
                )['stdout']
            )
            if iface_data.find(ifname) == -1:
                logging.error("Interface %s is absent" % ifname_short)
                ifaces_fail = True
            else:
                try:
                    if iface_data.find("inet %s" % iface['ip']) == -1:
                        logging.error(
                            "Interface %s does not have ip %s" % (
                                ifname_short, iface['ip']
                            )
                        )
                        ifaces_fail = True
                except KeyError:
                    if iface_data.find("inet ") != -1:
                        logging.error(
                            "Interface %s does have ip.  And it should not" %
                            ifname_short
                        )
                        ifaces_fail = True
                try:
                    if iface_data.find("brd %s" % iface['brd']) == -1:
                        logging.error(
                            "Interface %s does not have broadcast %s" % (
                                ifname_short, iface['brd']
                            )
                        )
                        ifaces_fail = True
                except KeyError:
                    pass
        self.assertEquals(ifaces_fail, False)

    @snapshot_errors
    def test_node_deletion(self):
        self._revert_nodes()
        cluster_name = 'node_deletion'
        node_name = 'slave1'
        nodes = {'controller': [node_name]}
        cluster_id = self._basic_provisioning(cluster_name, nodes)

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

    @snapshot_errors
    def test_network_verify(self):
        self._revert_nodes()
        cluster_name = 'net_verify'
        cluster_id = self._create_cluster(name=cluster_name)
        # Check network in empty cluster.
        task = self._run_network_verify(cluster_id)
        task = self._task_wait(task, 'Verify network in empty cluster',
                               20, True)
        self.assertEquals(task['status'], 'error')
        # Check network with one node.
        node_names = ['slave1', 'slave2']
        nailgun_slave_nodes = self._bootstrap_nodes(node_names)
        devops_nodes = [ci.environment.node[n] for n in node_names]
        self._update_nodes_in_cluster(cluster_id, [nailgun_slave_nodes[0]])
        task = self._run_network_verify(cluster_id)
        self._task_wait(task, 'Verify network in cluster with one node', 20)
        # Check network with two nodes.
        logging.info("Clear BROUTING table entries.")
        vlan = self._get_common_vlan(cluster_id)
        for node in devops_nodes:
            self._restore_vlan_in_ebtables(node.interfaces[0].target_dev,
                                           vlan, False)
        self._update_nodes_in_cluster(cluster_id, nailgun_slave_nodes)
        task = self._run_network_verify(cluster_id)
        self._task_wait(task, 'Verify network in cluster with two nodes',
                        60 * 2)
        # Check network with one blocked vlan.
        self._block_vlan_in_ebtables(devops_nodes, vlan)
        task = self._run_network_verify(cluster_id)
        task = self._task_wait(task,
                               'Verify network in cluster with blocked vlan',
                               60 * 2, True)
        self.assertEquals(task['status'], 'error')

    def _block_vlan_in_ebtables(self, devops_nodes, vlan):
        try:
            for node in devops_nodes:
                subprocess.check_output(
                    'sudo ebtables -t broute -A BROUTING -i %s -p 8021Q'
                    ' --vlan-id %s -j DROP' % (
                        node.interfaces[0].target_dev, vlan
                    ),
                    stderr=subprocess.STDOUT,
                    shell=True
                )
                self.addCleanup(self._restore_vlan_in_ebtables,
                                node.interfaces[0].target_dev, vlan)
        except subprocess.CalledProcessError as e:
            raise Exception("Can't block vlan %s for interface %s"
                            " via ebtables: %s" %
                            (vlan, node.interfaces[0].target_dev, e.output))

    def _get_common_vlan(self, cluster_id):
        """Find vlan that must be at all two nodes.
        """
        resp = self.client.get(
            "/api/networks/"
        )
        self.assertEquals(200, resp.getcode())
        for net in json.loads(resp.read()):
            if net['cluster_id'] == cluster_id:
                return net['vlan_start']
        raise Exception("Can't find vlan for cluster_id %s" % cluster_id)

    @staticmethod
    def _restore_vlan_in_ebtables(target_dev, vlan, log=True):
        try:
            subprocess.check_output(
                'sudo ebtables -t broute -D BROUTING -i %s -p 8021Q'
                ' --vlan-id %s -j DROP' % (
                    target_dev, vlan
                ),
                stderr=subprocess.STDOUT,
                shell=True
            )
        except subprocess.CalledProcessError as e:
            if log:
                logging.warn("Can't restore vlan %s for interface %s"
                             " via ebtables: %s" %
                             (vlan, target_dev, e.output))

    def _run_network_verify(self, cluster_id):
        logging.info(
            "Run network verifty in cluster %d",
            cluster_id
        )
        changes = self.client.put(
            "/api/clusters/%d/verify/networks/" % cluster_id
        )
        self.assertEquals(200, changes.getcode())
        return json.loads(changes.read())

    def _basic_provisioning(self, cluster_name, nodes_dict):
        self._clean_clusters()
        cluster_id = self._create_cluster(name=cluster_name)
        node_names = []
        for role in nodes_dict:
            node_names += nodes_dict[role]
        try:
            if len(node_names) > 1:
                if len(nodes_dict['controller']) == 1:
                    self.client.put(
                        "/api/clusters/%s/" % cluster_id,
                        {"mode": "multinode"}
                    )
                if len(nodes_dict['controller']) > 1:
                    self.client.put(
                        "/api/clusters/%s/" % cluster_id,
                        {"mode": "ha"}
                    )
        except KeyError:
            pass

        nodes = self._bootstrap_nodes(node_names)

        for role in nodes_dict:
            for n in nodes_dict[role]:
                slave = ci.environment.node[n]
                node = self._get_slave_node_by_devops_node(slave)
                self.client.put(
                    "/api/nodes/%s/" % node['id'],
                    {"role": role, "pending_addition": True}
                )

        self._update_nodes_in_cluster(cluster_id, nodes)
        task = self._launch_provisioning(cluster_id)

        self._task_wait(task, 'Installation')

        for role in nodes_dict:
            for n in nodes_dict[role]:
                slave = ci.environment.node[n]
                node = self._get_slave_node_by_devops_node(slave)
                ctrl_ssh = SSHClient()
                ctrl_ssh.connect_ssh(node['ip'], 'root', 'r00tme')
                ret = ctrl_ssh.execute('test -f /tmp/%s-file' % role)
                self.assertEquals(ret['exit_status'], 0)
        return cluster_id

    def _launch_provisioning(self, cluster_id):
        """Return hash with task description."""
        logging.info(
            "Launching provisioning on cluster %d",
            cluster_id
        )
        changes = self.client.put(
            "/api/clusters/%d/changes/" % cluster_id
        )
        self.assertEquals(200, changes.getcode())
        return json.loads(changes.read())

    def _task_wait(self, task, task_desc, timeout=70 * 60,
                   skip_error_status=False):
        timer = time.time()
        ready = False
        task_id = task['id']
        logging.info("Waiting task %r ..." % task_desc)
        while not ready:
            try:
                task = json.loads(
                    self.client.get("/api/tasks/%s" % task_id).read()
                )
            except ValueError:
                task = {'status': 'running'}
            if task['status'] == 'ready':
                logging.info("Task %r complete" % task_desc)
                ready = True
            elif task['status'] == 'error' and skip_error_status:
                logging.info("Task %r ended with error: %s" %
                             (task_desc, task['message']))
                ready = True
            elif task['status'] == 'running':
                if (time.time() - timer) > timeout:
                    raise Exception("Task %r timeout expired!" % task_desc)
                time.sleep(5)
            else:
                raise Exception("Task %s failed with status %r and msg: %s!" %
                                (task_desc, task['status'], task['message']))
        return task

    def _upload_sample_release(self):
        def _get_release_id():
            releases = json.loads(
                self.client.get("/api/releases/").read()
            )
            for r in releases:
                logging.debug("Found release name: %s" % r["name"])
                if r["name"] == "Folsom":
                    logging.debug("Sample release id: %s" % r["id"])
                    return r["id"]

        release_id = _get_release_id()
        if not release_id:
            raise Exception("Not implemented uploading of release")
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
        node_ids = [str(node['id']) for node in nodes]
        resp = self.client.put(
            "/api/clusters/%s" % cluster_id,
            data={"nodes": node_ids})
        self.assertEquals(200, resp.getcode())
        cluster = json.loads(self.client.get(
            "/api/clusters/%s" % cluster_id).read())
        nodes_in_cluster = [str(n['id']) for n in cluster['nodes']]
        self.assertEquals(sorted(node_ids), sorted(nodes_in_cluster))

    def _get_slave_node_by_devops_node(self, devops_node):
        """Return hash with nailgun slave node description if node
        register itself on nailgun. Otherwise return None.
        """
        response = self.client.get("/api/nodes/")
        nodes = json.loads(response.read())
        logging.debug("get_slave_node_by_devops_node: nodes at nailgun: %r" %
                      str(nodes))

        for n in nodes:
            for i in devops_node.interfaces:
                logging.debug("get_slave_node_by_devops_node: \
node.interfaces[n].mac_address: %r" % str(i.mac_address))
                if n['mac'].capitalize() == i.mac_address.capitalize():
                    n['devops_name'] = devops_node.name
                    return n
        return None

    def _bootstrap_nodes(self, devops_node_names=[]):
        """Start devops nodes and wait while they load boodstrap image
        and register on nailgun. Returns list of hashes with registred nailgun
        slave node descpriptions.
        """
        timer = time.time()
        timeout = 600

        slaves = []
        for node_name in devops_node_names:
            slave = ci.environment.node[node_name]
            logging.info("Starting slave node %r" % node_name)
            slave.start()
            slaves.append(slave)

        nodes = []
        while len(nodes) < len(slaves):
            nodes = []
            for slave in slaves:
                node = self._get_slave_node_by_devops_node(slave)
                if node is not None:
                    nodes.append(node)
                else:
                    logging.debug("Node %r not found" % node_name)
                if (time.time() - timer) > timeout:
                    raise Exception("Slave node agent failed to execute!")
                time.sleep(15)
                logging.info("Waiting for slave agent to run...")
        logging.debug("%d node(s) found" % len(nodes))
        return nodes

    def _check_cluster_status(self, ip):
        ctrl_ssh = SSHClient()
        ctrl_ssh.connect_ssh(ip, 'root', 'r00tme')
        ret = ctrl_ssh.execute('/usr/bin/nova-manage service list')
        nova_status = (
            (ret['exit_status'] == 0)
            and (''.join(ret['stdout']).count(":-)") == 5)
            and (''.join(ret['stdout']).count("XXX") == 0)
        )
        logging.debug("Nova check status: %d" % nova_status)
        ret = ctrl_ssh.execute('. /root/openrc; glance index')
        cirros_status = (
            (ret['exit_status'] == 0)
            and (''.join(ret['stdout']).count("TestVM") == 1)
        )
        logging.debug("Cirros check status: %d" % cirros_status)
        return (nova_status and cirros_status)

    def _revert_nodes(self):
        logging.info("Reverting to snapshot 'initial'")
        for node in ci.environment.nodes:
            try:
                node.stop()
            except:
                pass
        for node in ci.environment.nodes:
            node.restore_snapshot('initial')
            sleep(5)
