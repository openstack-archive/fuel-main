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
COOKBOOKS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "cooks", "cookbooks")
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

    def setUp(self):
        admin_node = ci.environment.node['admin']
        self.admin_host = str(admin_node.ip_address)
        cookbook_remote_path = os.path.join(SAMPLE_REMOTE_PATH, "sample-cook")
        mysql_remote_path = os.path.join(COOKBOOKS_PATH, "mysql")
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
        logging.info("Loading cookbooks to database...")
        with self.remote.sudo:
            for cmd in commands:
                res = self.remote.execute(cmd)
                if res['exit_status'] != 0:
                    self.remote.disconnect()
                    raise Exception("Command failed: %s" % str(res))

        self.remote.disconnect()

    def test_node_deploy(self):
        # TODO: move system installation in setUp
        slave = ci.environment.node['slave']
        self.slave_id = slave.interfaces[0].mac_address.replace(":", "").upper()

        logging.info("Starting slave node")
        slave.start()

        logging.info("Nailgun IP: %s" % self.admin_host)

        timer = time.time()
        timeout = 600
        while True:
            node = self.client.get(
                "http://%s:8000/api/nodes/%s" % (self.admin_host, self.slave_id)
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
                "http://%s:8000/api/clusters/1" % self.admin_host
            ))
        except ValueError:
            logging.info("No clusters found - creating test cluster...")
            cluster = self.client.post(
                "http://%s:8000/api/clusters" % self.admin_host,
                data='{ "name": "MyOwnPrivateCluster", "release": 1 }'
            )
            cluster = json.loads(cluster)

        resp = json.loads(self.client.put(
            "http://%s:8000/api/clusters/1" % self.admin_host,
            data='{ "nodes": ["%s"] }' % self.slave_id
        ))

        cluster = json.loads(self.client.get(
            "http://%s:8000/api/clusters/1" % self.admin_host
        ))
        if len(cluster["nodes"]) == 0:
            raise ValueError("Failed to add node into cluster")

        roles_uploaded = json.loads(self.client.get(
            "http://%s:8000/api/roles/" % self.admin_host
        ))
        roles_ids = [
            role["id"] for role in roles_uploaded \
                if role["recipes"][0].startswith("sample-cook") \
                or role["recipes"][0].startswith("mysql")
        ]

        resp = json.loads(self.client.put(
            "http://%s:8000/api/nodes/%s" % (self.admin_host, self.slave_id),
            data='{ "new_roles": %s, "redeployment_needed": true }' % str(roles_ids)
        ))
        if len(resp["new_roles"]) == 0:
            raise ValueError("Failed to assign roles to node")

        if node["status"] == "discover":
            logging.info("Node booted with bootstrap image.")
        elif node["status"] == "ready":
            logging.info("Node already installed.")
            self._slave_delete_test_file()

        logging.info("Provisioning...")
        task = json.loads(self.client.put(
            "http://%s:8000/api/clusters/1/changes/" % self.admin_host
        ))
        task_id = task['task_id']
        logging.info("Task created: %s" % task_id)
        logging.info("Waiting for completion of slave node software installation")
        timer = time.time()
        timeout = 1800
        while True:
            try:
                task = self.client.get(
                    "http://%s:8000/api/tasks/%s/" % (self.admin_host, task_id)
                )
                logging.info(str(task))
                task = json.loads(task)
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
            "http://%s:8000/api/nodes/%s" % (self.admin_host, self.slave_id)
        ))
        self.slave_host = node["ip"]

        logging.info("Waiting for SSH access on %s" % self.slave_host)
        wait(lambda: tcp_ping(self.slave_host, 22), timeout=1800)
        self.remote.connect_ssh(self.slave_host, self.slave_user, self.slave_passwd)

        # check if recipes executed
        ret = self.remote.execute("test -f /tmp/chef_success")
        if ret['exit_status'] != 0:
            raise Exception("Recipes failed to execute!")

        # check mysql running
        #db = MySQLdb.connect(passwd="test", user="root", host=self.slave_host)
        #print db

        # check recipes execution order
        ret = self.remote.execute("cat /tmp/chef_success")
        if [out.strip() for out in ret['stdout']] != ['monitor', 'default', 'compute']:
            raise Exception("Recipes executed in a wrong order: %s!" \
                % str(ret['stdout']))

        # chech node status
        node = json.loads(self.client.get(
            "http://%s:8000/api/nodes/%s" % (self.admin_host, self.slave_id)
        ))
        self.assertEqual(node["status"], "ready")
        self.remote.disconnect()

    def _slave_delete_test_file(self):
        logging.info("Deleting test file...")
        slave_client = SSHClient()
        slave_client.connect_ssh(self.slave_host, self.slave_user, self.slave_passwd)
        res = slave_client.execute("rm -rf /tmp/chef_success")
        slave_client.disconnect()
