import shlex
import os
import sys
import logging
import time
import json
import urllib2
from unittest import TestCase
from subprocess import Popen, PIPE

import paramiko

from devops.helpers import wait, tcp_ping, http

from . import ci
from integration.helpers import HTTPClient, SSHClient

logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s', level=logging.DEBUG)

AGENT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "agent")
DEPLOY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "deploy")
COOKBOOKS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "cookbooks")
SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "ci")
SAMPLE_REMOTE_PATH = "/home/ubuntu"


class StillPendingException(Exception):
    pass


class TestNode(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestNode, self).__init__(*args, **kwargs)
        self.client = HTTPClient()
        self.remote = SSHClient()
        self.admin_host = None
        self.admin_user = "ubuntu"
        self.admin_passwd = "r00tme"
        self.slave_host = None
        self.slave_user = "root"
        self.slave_passwd = "r00tme"

    def test_node(self):
        admin_node = ci.environment.node['admin']
        self.admin_host = admin_ip = str(admin_node.ip_address)
        slave = ci.environment.node['slave']
        slave_id = slave.interfaces[0].mac_address.replace(":", "").upper()
        logging.info("Starting slave node")
        slave.start()

        logging.info("Nailgun IP: %s" % admin_ip)
        self._load_sample_admin()

        timer = time.time()
        timeout = 600
        while True:
            node = self.client.get(
                "http://%s:8000/api/nodes/%s" % (admin_ip, slave_id),
                log=True
            )
            if not node.startswith("404"):
                logging.info("Node found")
                node = json.loads(node)
                self.slave_host = node["ip"]
                break
            else:
                logging.info("Node not found")
                if (time.time() - timer) > timeout:
                    raise Exception("Slave node agent failed to execute!")
                time.sleep(15)
                logging.info("Waiting for slave agent to run...")

        try:
            cluster = json.loads(self.client.get(
                "http://%s:8000/api/clusters/1" % admin_ip,
                log=True
            ))
        except ValueError:
            logging.info("No clusters found - creating test cluster...")
            cluster = self.client.post(
                "http://%s:8000/api/clusters" % admin_ip,
                data='{ "name": "MyOwnPrivateCluster", "release": 1 }',
                log=True
            )
            cluster = json.loads(cluster)

        resp = json.loads(self.client.put(
            "http://%s:8000/api/clusters/1" % admin_ip,
            data='{ "nodes": ["%s"] }' % slave_id
        ))

        cluster = json.loads(self.client.get(
            "http://%s:8000/api/clusters/1" % admin_ip
        ))
        if len(cluster["nodes"]) == 0:
            raise ValueError("Failed to add node into cluster")

        resp = json.loads(self.client.put(
            "http://%s:8000/api/nodes/%s" % (admin_ip, slave_id),
            data='{ "new_roles": [1, 2], "redeployment_needed": true }'
        ))
        if len(resp["new_roles"]) == 0:
            raise ValueError("Failed to assign roles to node")

        if node["os_platform"] == "ubuntu":
            logging.info("Node booted with bootstrap image.")
        if node["os_platform"] == "centos":
            logging.info("Node already installed.")
            self._slave_delete_test_file()

        logging.info("Provisioning...")
        task = json.loads(self.client.put(
            "http://%s:8000/api/clusters/1/changes/" % admin_ip,
            log=True
        ))
        task_id = task['task_id']
        logging.info("Task created: %s" % task_id)
        logging.info("Waiting for completion of slave node software installation")
        timer = time.time()
        timeout = 1800
        while True:
            try:
                task = json.loads(self.client.get(
                    "http://%s:8000/api/tasks/%s/" % (admin_ip, task_id)
                ))
                if not task['ready']:
                    raise StillPendingException("Task %s is still pending")
                if task.get('error'):
                    raise Exception(
                        "Task %s failed!\n %s" %
                        (task['task_id'], str(task)),
                    )
                break
            except StillPendingException:
                if (time.time() - timer) > timeout:
                    raise Exception("Task pending timeout!")
                time.sleep(30)

        node = json.loads(self.client.get(
            "http://%s:8000/api/nodes/%s" % (admin_ip, slave_id),
            log=True
        ))
        self.slave_host = node["ip"]

        logging.info("Waiting for SSH access on %s" % self.slave_host)
        wait(lambda: tcp_ping(self.slave_host, 22), timeout=1800)
        self.remote.connect_ssh(self.slave_host, self.slave_user, self.slave_passwd)

        # check if recipes executed
        ret = self.remote.execute("test -f /tmp/chef_success")
        if ret['exit_status'] != 0:
            raise Exception("Recipes failed to execute!")
        
        # check recipes execution order
        ret = self.remote.execute("cat /tmp/chef_success")
        if [out.strip() for out in ret['stdout']] != ['monitor', 'default', 'compute']:
            raise Exception("Recipes executed in a wrong order: %s!" \
                % str(ret['stdout']))

        self.remote.disconnect()

    def test_mysql_cookbook(self):
        pass

    def _admin_resync_db(self):
        logging.info("Nailgun database resyncing...")
        admin_client = SSHClient()
        admin_client.connect_ssh(self.admin_host, self.admin_user, self.admin_passwd)
        commands = [
            "rm -rf /opt/nailgun/nailgun.sqlite",
            "/opt/nailgun-venv/bin/python /opt/nailgun/manage.py syncdb --noinput",
            "chown nailgun:nailgun /opt/nailgun/nailgun.sqlite",
        ]
        with admin_client.sudo:
            for cmd in commands:
                res = admin_client.execute(cmd)
                if res['exit_status'] != 0:
                    raise Exception("Command failed: %s" % str(res))
        logging.info("Done.")
        admin_client.disconnect()

    def _slave_run_agent(self):
        logging.info("Running slave node agent...")
        slave_client = SSHClient()
        slave_client.connect_ssh(self.admin_host, self.admin_user, self.admin_passwd)

        with slave_client.sudo:
            res = slave_client.execute("/opt/nailgun/bin/agent -c /opt/nailgun/bin/agent_config.rb")
            if res['exit_status'] != 0:
                raise Exception("Command failed: %s" % str(res))
        logging.info("Done.")
        slave_client.disconnect()

    def _slave_delete_test_file(self):
        logging.info("Deleting test file...")
        slave_client = SSHClient()
        slave_client.connect_ssh(self.admin_host, self.admin_user, self.admin_passwd)

        with slave_client.sudo:
            res = slave_client.execute("test -f /tmp/chef_success && rm -rf /tmp/chef_success")
            if res['exit_status'] != 0:
                raise Exception("Command failed: %s" % str(res))
        logging.info("Done.")
        slave_client.disconnect()        


    def _load_sample_admin(self):
        cookbook_remote_path = os.path.join(SAMPLE_REMOTE_PATH, "sample-cook")
        release_remote_path = os.path.join(SAMPLE_REMOTE_PATH, "sample-release.json")
        self.remote.connect_ssh(self.admin_host, self.admin_user, self.admin_passwd)
        self.remote.rmdir(cookbook_remote_path)
        self.remote.rmdir(os.path.join(SAMPLE_REMOTE_PATH, "cookbooks"))
        self.remote.rmdir(os.path.join(SAMPLE_REMOTE_PATH, "solo"))
        self.remote.scp(
            os.path.join(SAMPLE_PATH, "sample-release.json"),
            release_remote_path
        )
        self.remote.mkdir(os.path.join(SAMPLE_REMOTE_PATH, "solo"))
        self.remote.mkdir(os.path.join(SAMPLE_REMOTE_PATH, "solo/config"))
        self.remote.scp_d(
            os.path.join(SAMPLE_PATH, "sample-cook"),
            SAMPLE_REMOTE_PATH
        )
        self.remote.scp_d(
            COOKBOOKS_PATH,
            SAMPLE_REMOTE_PATH
        )
        commands = [
            "/opt/nailgun/bin/install_cookbook %s" % cookbook_remote_path,
            "/opt/nailgun/bin/create_release %s" % release_remote_path
        ]

        self._admin_resync_db()
        with self.remote.sudo:
            for cmd in commands:
                res = self.remote.execute(cmd)
                if res['exit_status'] != 0:
                    self.remote.disconnect()
                    raise Exception("Command failed: %s" % str(res))

        self.remote.disconnect()
