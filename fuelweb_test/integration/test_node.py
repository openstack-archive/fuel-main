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
import urllib2
from time import sleep

from devops.helpers import wait, tcp_ping, http
from fuelweb_test.integration import ci
from fuelweb_test.integration.base import Base
from fuelweb_test.helpers import SSHClient, HTTPClient, LogServer
from fuelweb_test.root import root

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
    """ Decorator to snapshot nodes when error occurred in test.
    """
    def decorator(*args, **kwagrs):
        def save_logs(filename):
            try:
                if not getattr(ci, 'export_logs_dir', ''):
                    return
                logfile_name = os.path.abspath(
                    os.path.join(ci.export_logs_dir, filename + ".tar.gz")
                )
                if not os.path.isdir(os.path.dirname(logfile_name)):
                    os.makedirs(os.path.dirname(logfile_name))
                logging.info('Saving logs to "%s" file' % logfile_name)
                remote_log = urllib2.urlopen(
                    "http://%s:8000/api/logs/package"
                    % ci.environment.node['admin'].ip_address
                )
                with open(logfile_name, 'w') as f:
                    f.write(remote_log.read())
            except Exception, e:
                logging.warn(
                    'Cannot save logfile "%s": %s' % (logfile_name, e)
                )

        timestamp = str(int(time.time() * 100))
        try:
            func(*args, **kwagrs)
        except Exception, e:
            ss_name = 'error-%s' % timestamp
            desc = "Failed in method '%s'" % func.__name__
            exc = list(sys.exc_info())
            exc[2] = exc[2].tb_next
            logging.warn('Some raise occurred in method "%s"' % func.__name__)
            logging.warn(''.join(traceback.format_exception(*exc)))
            save_logs("failed-%s-%s" % (func.__name__, timestamp))
            for node in ci.environment.nodes:
                logging.info("Creating snapshot '%s' for node %s" %
                             (ss_name, node.name))
                node.save_snapshot(ss_name, desc)
            raise e, None, sys.exc_info()[2].tb_next
        save_logs("ok-%s-%s" % (func.__name__, timestamp))
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

    def tearDown(self):
        self._wait_for_threads()
        try:
            self._stop_logserver()
        except AttributeError:
            pass

    def _start_logserver(self, handler=None):
        self._logserver_status = False
        if not handler:
            """
            We define log message handler in such a way
            assuming that if at least one message is received
            logging works fine.
            """
            def handler(message):
                self._logserver_status = True

        self.logserver = LogServer(
            address=self.get_host_node_ip(),
            port=5514
        )
        self.logserver.set_handler(handler)
        self.logserver.start()

    def _stop_logserver(self):
        self.logserver.stop()
        self._logserver_status = False

    def _status_logserver(self):
        return self._logserver_status

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
    def test_simple_cluster_flat(self):
        logging.info("Testing simple flat installation.")
        self._revert_nodes()
        cluster_name = 'simple_flat'
        nodes = {'controller': ['slave1'], 'compute': ['slave2']}
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        slave = ci.environment.node['slave1']
        node = self._get_slave_node_by_devops_node(slave)
        wait(lambda: self._check_cluster_status(node['ip'], 5), timeout=300)

        logging.info("Verifying networks for simple flat installation.")
        vlans = self._get_cluster_vlans(cluster_id)
        slave2 = ci.environment.node['slave2']
        for vlan in vlans:
            for n in (slave, slave2):
                self._restore_vlan_in_ebtables(
                    n.interfaces[0].target_dev,
                    vlan,
                    False
                )
        task = self._run_network_verify(cluster_id)
        self._task_wait(task, 'Verify network simple flat', 60 * 2)

    @snapshot_errors
    def test_simple_cluster_vlan(self):
        logging.info("Testing simple vlan installation.")
        self._revert_nodes()
        cluster_name = 'simple_vlan'
        nodes = {'controller': ['slave1'], 'compute': ['slave2']}
        self._create_cluster(name=cluster_name, net_manager="VlanManager")
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        slave = ci.environment.node['slave1']
        node = self._get_slave_node_by_devops_node(slave)
        wait(lambda: self._check_cluster_status(node['ip'], 5, 8), timeout=300)

        logging.info("Verifying networks for simple vlan installation.")
        vlans = self._get_cluster_vlans(cluster_id)
        slave2 = ci.environment.node['slave2']
        for vlan in vlans:
            for n in (slave, slave2):
                self._restore_vlan_in_ebtables(
                    n.interfaces[0].target_dev,
                    vlan,
                    False
                )
        task = self._run_network_verify(cluster_id)
        self._task_wait(task, 'Verify network simple vlan', 60 * 2)

    @snapshot_errors
    def test_ha_cluster_flat(self):
        logging.info("Testing ha flat installation.")
        self._revert_nodes()
        cluster_name = 'ha_flat'
        nodes = {
            'controller': ['slave1', 'slave2', 'slave3'],
            'compute': ['slave4', 'slave5']
        }
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        logging.info("Checking cluster status on slave1")
        slave = ci.environment.node['slave1']
        node = self._get_slave_node_by_devops_node(slave)
        wait(lambda: self._check_cluster_status(node['ip'], 13), timeout=300)

        logging.info("Verifying networks for ha flat installation.")
        vlans = self._get_cluster_vlans(cluster_id)
        slave2 = ci.environment.node['slave2']
        slave3 = ci.environment.node['slave3']
        slave4 = ci.environment.node['slave4']
        slave5 = ci.environment.node['slave5']
        for vlan in vlans:
            for n in (slave, slave2, slave3, slave4, slave5):
                self._restore_vlan_in_ebtables(
                    n.interfaces[0].target_dev,
                    vlan,
                    False
                )
        task = self._run_network_verify(cluster_id)
        self._task_wait(task, 'Verify network ha flat', 60 * 2)

    @snapshot_errors
    def test_ha_cluster_vlan(self):
        logging.info("Testing ha vlan installation.")
        self._revert_nodes()
        cluster_name = 'ha_vlan'
        nodes = {
            'controller': ['slave1', 'slave2', 'slave3'],
            'compute': ['slave4', 'slave5']
        }
        self._create_cluster(name=cluster_name, net_manager="VlanManager")
        cluster_id = self._basic_provisioning(cluster_name, nodes)
        slave = ci.environment.node['slave1']
        node = self._get_slave_node_by_devops_node(slave)
        wait(
            lambda: self._check_cluster_status(node['ip'], 13, 8),
            timeout=300
        )

        logging.info("Verifying networks for ha vlan installation.")
        vlans = self._get_cluster_vlans(cluster_id)
        slave2 = ci.environment.node['slave2']
        slave3 = ci.environment.node['slave3']
        slave4 = ci.environment.node['slave4']
        slave5 = ci.environment.node['slave5']
        for vlan in vlans:
            for n in (slave, slave2, slave3, slave4, slave5):
                self._restore_vlan_in_ebtables(
                    n.interfaces[0].target_dev,
                    vlan,
                    False
                )
        task = self._run_network_verify(cluster_id)
        self._task_wait(task, 'Verify network ha vlan', 60 * 2)

    @snapshot_errors
    def test_network_config(self):
        self._revert_nodes()
        self._clean_clusters()
        self._basic_provisioning('network_config', {'controller': ['slave1']})

        slave = ci.environment.node['slave1']
        keyfiles = ci.environment.node['admin'].metadata['keyfiles']
        node = self._get_slave_node_by_devops_node(slave)
        ctrl_ssh = SSHClient()
        ctrl_ssh.connect_ssh(node['ip'], 'root', key_filename=keyfiles)
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
    def test_network_verify_with_blocked_vlan(self):
        self._revert_nodes()
        cluster_name = 'net_verify'
        cluster_id = self._create_cluster(name=cluster_name)
        node_names = ['slave1', 'slave2']
        nailgun_slave_nodes = self._bootstrap_nodes(node_names)
        devops_nodes = [ci.environment.node[n] for n in node_names]
        logging.info("Clear BROUTING table entries.")
        vlans = self._get_cluster_vlans(cluster_id)
        for vlan in vlans:
            for node in devops_nodes:
                for interface in node.interfaces:
                    self._restore_vlan_in_ebtables(interface.target_dev,
                                                   vlan, False)
        self._update_nodes_in_cluster(cluster_id, nailgun_slave_nodes)
        for node in devops_nodes:
            for interface in node.interfaces:
                self._block_vlan_in_ebtables(interface.target_dev, vlans[0])
        task = self._run_network_verify(cluster_id)
        task = self._task_wait(task,
                               'Verify network in cluster with blocked vlan',
                               60 * 2, True)
        self.assertEquals(task['status'], 'error')

    @snapshot_errors
    def test_multinic_bootstrap_booting(self):
        self._revert_nodes()
        slave = filter(lambda n: n.name != 'admin' and len(n.interfaces) > 1,
                       ci.environment.nodes)[0]
        nodename = slave.name
        logging.info("Using node %r with %d interfaces", nodename,
                     len(slave.interfaces))
        slave.stop()
        admin = ci.environment.node['admin']
        macs = [i.mac_address for i in slave.interfaces]
        logging.info("Block all MACs: %s.",
                     ', '.join([m for m in macs]))
        for mac in macs:
            self._block_mac_in_ebtables(mac)
            self.addCleanup(self._restore_mac_in_ebtables, mac)
        for mac in macs:
            logging.info("Trying to boot node %r via interface with MAC %s...",
                         nodename, mac)
            self._restore_mac_in_ebtables(mac)
            slave.start()
            nailgun_slave = self._bootstrap_nodes([nodename])[0]
            self.assertEqual(mac.upper(), nailgun_slave['mac'].upper())
            slave.stop()
            admin.restore_snapshot('initial')
            self._block_mac_in_ebtables(mac)

    @staticmethod
    def _block_mac_in_ebtables(mac):
        try:
            subprocess.check_output(
                'sudo ebtables -t filter -A FORWARD -s %s -j DROP' % mac,
                stderr=subprocess.STDOUT,
                shell=True
            )
            logging.debug("MAC %s blocked via ebtables.", mac)
        except subprocess.CalledProcessError as e:
            raise Exception("Can't block mac %s via ebtables: %s",
                            mac, e.output)

    @staticmethod
    def _restore_mac_in_ebtables(mac):
        try:
            subprocess.check_output(
                'sudo ebtables -t filter -D FORWARD -s %s -j DROP' % mac,
                stderr=subprocess.STDOUT,
                shell=True
            )
            logging.debug("MAC %s unblocked via ebtables.", mac)
        except subprocess.CalledProcessError as e:
            logging.warn("Can't restore mac %s via ebtables: %s",
                         mac, e.output)

    def _block_vlan_in_ebtables(self, target_dev, vlan):
        try:
            subprocess.check_output(
                'sudo ebtables -t broute -A BROUTING -i %s -p 8021Q'
                ' --vlan-id %s -j DROP' % (
                    target_dev, vlan
                ),
                stderr=subprocess.STDOUT,
                shell=True
            )
            self.addCleanup(self._restore_vlan_in_ebtables,
                            target_dev, vlan)
            logging.debug("Vlan %s on interface %s blocked via ebtables.",
                          vlan, target_dev)
        except subprocess.CalledProcessError as e:
            raise Exception("Can't block vlan %s for interface %s"
                            " via ebtables: %s" %
                            (vlan, target_dev, e.output))

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

    def _get_cluster_vlans(self, cluster_id):
        resp = self.client.get("/api/networks/?cluster_id=%d" % cluster_id)
        self.assertEquals(200, resp.getcode())
        cluster_vlans = []
        for n in json.loads(resp.read()):
            amount = n.get('amount', 1)
            cluster_vlans.extend(range(n['vlan_start'],
                                       n['vlan_start'] + amount))
        self.assertNotEqual(cluster_vlans, [])
        return cluster_vlans

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
            logging.debug("Vlan %s on interface %s unblocked via ebtables.",
                          vlan, target_dev)
        except subprocess.CalledProcessError as e:
            if log:
                logging.warn("Can't restore vlan %s for interface %s"
                             " via ebtables: %s" %
                             (vlan, target_dev, e.output))

    def _run_network_verify(self, cluster_id):
        logging.info(
            "Run network verify in cluster %d",
            cluster_id
        )
        resp = self.client.get("/api/networks/?cluster_id=%d" % cluster_id)
        self.assertEquals(200, resp.getcode())
        networks = json.loads(resp.read())
        changes = self.client.put(
            "/api/clusters/%d/verify/networks/" % cluster_id, networks
        )
        self.assertEquals(200, changes.getcode())
        return json.loads(changes.read())

    def _basic_provisioning(self, cluster_name, nodes_dict):
        self._start_logserver()
        self._clean_clusters()
        cluster_id = self._create_cluster(name=cluster_name)

        # Here we updating cluster editable attributes
        # In particular we set extra syslog server
        response = self.client.get(
            "/api/clusters/%s/attributes/" % cluster_id
        )
        attrs = json.loads(response.read())
        attrs["editable"]["syslog"]["syslog_server"]["value"] = \
            self.get_host_node_ip()
        attrs["editable"]["syslog"]["syslog_port"]["value"] = \
            self.logserver.bound_port()
        self.client.put(
            "/api/clusters/%s/attributes/" % cluster_id,
            attrs
        )

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

        logging.info("Checking role files on slave nodes")
        keyfiles = ci.environment.node['admin'].metadata['keyfiles']
        for role in nodes_dict:
            for n in nodes_dict[role]:
                logging.info("Checking /tmp/%s-file on %s" % (role, n))
                slave = ci.environment.node[n]
                node = self._get_slave_node_by_devops_node(slave)
                logging.debug("Trying to connect to %s via ssh" % node['ip'])
                ctrl_ssh = SSHClient()
                ctrl_ssh.connect_ssh(node['ip'], 'root', key_filename=keyfiles)
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
        logtimer = timer
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
                logging.info("Task %r failed with message: %s",
                             task_desc, task.get('message'))
                ready = True
            elif task['status'] == 'running':
                if (time.time() - timer) > timeout:
                    raise Exception("Task %r timeout expired!" % task_desc)
                time.sleep(5)
            else:
                raise Exception("Task %s failed with status %r and msg: %s!" %
                                (task_desc, task['status'],
                                 task.get('message')))

            if (time.time() - logtimer) > 120:
                logtimer = time.time()
                logging.debug("Task %s status: %s progress: %s timer: %s",
                              task.get('id'),
                              task.get('status'),
                              task.get('progress'),
                              (time.time() - timer))

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

    def _create_cluster(self, name='default',
                        release_id=None, net_manager="FlatDHCPManager"):
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
            self.client.put(
                "/api/clusters/%s/" % cluster_id,
                {'net_manager': net_manager}
            )
            if net_manager == "VlanManager":
                response = self.client.get(
                    "/api/networks/?cluster_id=%d" % cluster_id
                )
                networks = json.loads(response.read())
                flat_net = [n for n in networks if n['name'] == 'fixed']
                flat_net[0]['amount'] = 8
                flat_net[0]['network_size'] = 16
                self.client.put(
                    "/api/clusters/%d/save/networks/" % cluster_id, flat_net
                )
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

        logging.debug("get_slave_node_by_devops_node: "
                      "found nodes: %s", str([n['mac'] for n in nodes]))

        for n in nodes:
            logging.debug("get_slave_node_by_devops_node: looking for %s",
                          n['mac'])
            for i in devops_node.interfaces:
                logging.debug("get_slave_node_by_devops_node: checking: %s",
                              str(i.mac_address))

                if n['mac'].capitalize() == i.mac_address.capitalize():
                    logging.debug("get_slave_node_by_devops_node: matched")
                    logging.debug("get_slave_node_by_devops_node: %s",
                                  json.dumps(n, indent=4))

                    n['devops_name'] = devops_node.name
                    return n
        logging.debug("get_slave_node_by_devops_node: node %s not found",
                      devops_node.name)
        return None

    def _bootstrap_nodes(self, devops_node_names=[], timeout=600):
        """Start devops nodes and wait while they load boodstrap image
        and register on nailgun. Returns list of hashes with registred nailgun
        slave node descpriptions.
        """
        timer = time.time()

        slaves = []
        for node_name in devops_node_names:
            slave = ci.environment.node[node_name]
            logging.info("Starting slave node %r", node_name)
            slave.start()
            slaves.append(slave)

        nodes = []
        full_nodes_len = len(slaves)
        while True:
            for slave in list(slaves):
                node = self._get_slave_node_by_devops_node(slave)
                if node is not None:
                    nodes.append(node)
                    slaves.remove(slave)
                    logging.debug("Node %s found", node['mac'])
                else:
                    logging.debug("Node %s not bootstrapped yet", slave.name)

            logging.debug("Bootstrapped nodes: %s",
                          str([n['mac'] for n in nodes]))
            if (time.time() - timer) > timeout:
                raise Exception("Bootstrap nodes discovery failed by timeout."
                                " Nodes: %s" %
                                ', '.join([n.name for n in slaves]))

            if len(nodes) == full_nodes_len:
                break

            logging.info("Waiting bootstraping slave nodes: timer: %s",
                         (time.time() - timer))
            time.sleep(15)

        return nodes

    def _check_cluster_status(self, ip, smiles_count, networks_count=1):

        logging.info("Checking cluster status: ip=%s smiles=%s networks=%s",
                     ip, smiles_count, networks_count)

        keyfiles = ci.environment.node['admin'].metadata['keyfiles']
        ctrl_ssh = SSHClient()
        ctrl_ssh.connect_ssh(ip, 'root', key_filename=keyfiles)
        ret = ctrl_ssh.execute('/usr/bin/nova-manage service list')
        nova_status = (
            (ret['exit_status'] == 0)
            and (''.join(ret['stdout']).count(":-)") == smiles_count)
            and (''.join(ret['stdout']).count("XXX") == 0)
        )
        if not nova_status:
            logging.warn("Nova check fails:\n%s" % ret['stdout'])
        ret = ctrl_ssh.execute('. /root/openrc; glance index')
        cirros_status = (
            (ret['exit_status'] == 0)
            and (''.join(ret['stdout']).count("TestVM") == 1)
        )
        if not cirros_status:
            logging.warn("Cirros check fails:\n%s" % ret['stdout'])
        ret = ctrl_ssh.execute('/usr/bin/nova-manage network list')
        nets_status = (
            (ret['exit_status'] == 0)
            and (len(ret['stdout']) == networks_count + 1)
        )
        if not nets_status:
            logging.warn("Networks check fails:\n%s" % ret['stdout'])
        return (nova_status and
                cirros_status and
                nets_status and
                self._status_logserver()
                )

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
