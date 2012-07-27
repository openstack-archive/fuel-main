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

    def test_node(self):
        admin_node = ci.environment.node['admin']
        admin_ip = str(admin_node.ip_address)
        slave = ci.environment.node['slave']
        slave_id = slave.interfaces[0].mac_address.replace(":", "").upper()
        logging.info("Starting slave node")
        slave.start()

        logging.info("Nailgun IP: %s" % admin_ip)
        self._load_sample_admin(
            host=admin_ip,
            user="ubuntu",
            passwd="r00tme"
        )

        while True:
            logging.info("Waiting for slave agent to run...")
            nodes = json.loads(self.client.get(
                "http://%s:8000/api/nodes" % admin_ip
            ))
            if len(nodes) > 0:
                logging.info("Node found")
                break
            else:
                time.sleep(15)

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
            print cluster
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

        logging.info("Provisioning...")
        task = json.loads(self.client.put(
            "http://%s:8000/api/clusters/1/changes/" % admin_ip,
            log=True
        ))
        task_id = task['task_id']
        logging.info("Task created: %s" % task_id)
        logging.info("Waiting for completion of slave node software installation")
        while True:
            try:
                task = json.loads(self.client.get(
                    "http://%s:8000/api/tasks/%s/" % (admin_ip, task_id)
                ))
                if not task['ready']:
                    raise StillPendingException("Task %s is still pending")
                if not task['error'] == "":
                    raise Exception(
                        "Task %s failed!\n %s" %
                        (task['task_id'], str(task)),
                    )
                break
            except StillPendingException:
                time.sleep(30)

        node = task = json.loads(self.client.get(
            "http://%s:8000/api/nodes/%s" % (admin_ip, slave_id),
            log=True
        ))
        logging.info("Waiting for SSH access on %s" % node["ip"])
        wait(lambda: tcp_ping(node["ip"], 22), timeout=1800)
        self.remote.connect_ssh(node["ip"], "root", "r00tme")

        # check if recipes executed
        ret = self.remote.exec_cmd("test -f /tmp/chef_success")
        if ret['exit_status'] != 0:
            raise Exception("Recipes failed to execute!")
        """
        # check recipes execution order
        ret = self.remote.exec_cmd("cat /tmp/chef_success")
        if [out.strip() for out in ret['stdout']] != ['monitor', 'default', 'compute']:
            raise Exception("Recipes executed in a wrong order: %s!" \
                % str(ret['stdout']))

        # check passwords
        self.remote.exec_cmd("tar -C /root -xvf /root/nodes.tar.gz")
        ret = self.remote.exec_cmd("cat /root/nodes/`ls nodes` && echo")
        solo_json = json.loads(ret['stdout'][0])
        gen_pwd = solo_json['service']['password']
        if not gen_pwd or gen_pwd == 'password':
            raise Exception("Password generation failed!")
        """

        self.remote.disconnect()

    def _load_sample_admin(self, host, user, passwd):
        cookbook_remote_path = os.path.join(SAMPLE_REMOTE_PATH, "sample-cook")
        release_remote_path = os.path.join(SAMPLE_REMOTE_PATH, "sample-release.json")
        self.remote.connect_ssh(host, user, passwd)
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
            #"rm -rf /opt/nailgun/nailgun.sqlite",
            #"/opt/nailgun-venv/bin/python /opt/nailgun/manage.py syncdb --noinput",
            #"chown nailgun:nailgun /opt/nailgun/nailgun.sqlite",
            "/opt/nailgun/bin/install_cookbook %s" % cookbook_remote_path,
            "/opt/nailgun/bin/create_release %s" % release_remote_path
        ]

        with self.remote.sudo:
            for cmd in commands:
                res = self.remote.exec_cmd(cmd)
                if res['exit_status'] != 0:
                    self.remote.disconnect()
                    raise Exception("Command failed: %s" % str(res))

        self.remote.disconnect()
