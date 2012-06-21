import shlex
import os
import sys
import logging
import time
import json
import urllib2
from unittest import TestCase
from subprocess import Popen, PIPE

from . import ci
from devops.helpers import wait, tcp_ping, http
from integration.helpers import HTTPTestCase, SSHTestCase

import paramiko

logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s', level=logging.DEBUG)

SOLO_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "agent")
DEPLOY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "deploy")
COOKBOOKS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "cookbooks")
SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "ci")
SAMPLE_REMOTE_PATH = "/home/ubuntu"

class StillPendingException(Exception):
    pass

class TestNode(HTTPTestCase, SSHTestCase):
    def test_node(self):
        cookbook_remote_path = os.path.join(SAMPLE_REMOTE_PATH, "sample-cook")
        release_remote_path = os.path.join(SAMPLE_REMOTE_PATH, "sample-release.json")

        host = str(ci.environment.node['admin'].ip_address)
        self.connect_ssh(host, "ubuntu", "r00tme")

        self.rmdir(cookbook_remote_path)
        self.rmdir(os.path.join(SAMPLE_REMOTE_PATH, "cookbooks"))
        self.rmdir(os.path.join(SAMPLE_REMOTE_PATH, "solo"))
        
        self.scp(
            os.path.join(SAMPLE_PATH, "sample-release.json"),
            release_remote_path
        )

        self.mkdir(os.path.join(SAMPLE_REMOTE_PATH, "solo"))
        self.mkdir(os.path.join(SAMPLE_REMOTE_PATH, "solo/config"))        

        self.scp(
            DEPLOY_PATH,
            os.path.join(SAMPLE_REMOTE_PATH, "deploy")
        )
        self.scp(
            os.path.join(SOLO_PATH, "solo.json"),
            os.path.join(SAMPLE_REMOTE_PATH, "solo", "config", "solo.json")
        )
        self.scp(
            os.path.join(SOLO_PATH, "solo.rb"),
            os.path.join(SAMPLE_REMOTE_PATH, "solo", "config", "solo.rb")
        )

        self.scp_d(
            os.path.join(SAMPLE_PATH, "sample-cook"),
            SAMPLE_REMOTE_PATH
        )
        self.scp_d(
            COOKBOOKS_PATH,
            SAMPLE_REMOTE_PATH
        )

        self.aquire_sudo()

        commands = [
            "rm -rf /opt/nailgun/nailgun.sqlite",
            "source /opt/nailgun-venv/bin/activate",
            "python /opt/nailgun/manage.py syncdb --noinput",
            "deactivate",
            "cat /opt/nailgun/.ssh/id_rsa.pub > /root/.ssh/authorized_keys",
            "chmod 600 /root/.ssh/authorized_keys",
            "chown nailgun:nailgun /opt/nailgun/nailgun.sqlite",
            "/opt/nailgun/bin/install_cookbook %s" % cookbook_remote_path,
            "/opt/nailgun/bin/create_release %s" % release_remote_path,
            "cp %s/deploy /opt/nailgun/bin" % SAMPLE_REMOTE_PATH,
            "chmod 775 /opt/nailgun/bin/deploy",
            "chown nailgun:nailgun /opt/nailgun/bin/deploy",
            "rm /tmp/chef_success",
            "chef-solo -l debug -c %s -j %s" % (
                os.path.join(SAMPLE_REMOTE_PATH, "solo", "config", "solo.rb"),
                os.path.join(SAMPLE_REMOTE_PATH, "solo", "config", "solo.json")
            ),
        ]

        for cmd in commands:
            self.exec_cmd(cmd)

        cluster = json.loads(self.client.post(
            "http://%s:8000/api/clusters" % host,
            data='{ "name": "MyOwnPrivateCluster", "release": 1 }'
        ))

        nodes = json.loads(self.client.get(
            "http://%s:8000/api/nodes" % host
        ))
        if len(nodes) == 0:
            raise ValueError("Nodes list is empty")
        node_id = nodes[0]['id']

        resp = json.loads(self.client.put(
            "http://%s:8000/api/clusters/1" % host,
            data='{ "nodes": ["%s"] }' % node_id
        ))

        cluster = json.loads(self.client.get(
            "http://%s:8000/api/clusters/1" % host
        ))
        if len(cluster["nodes"]) == 0:
            raise ValueError("Failed to add node into cluster")

        resp = json.loads(self.client.put(
            "http://%s:8000/api/nodes/%s" % (host, node_id),
            data='{ "roles": [1, 2] }'
        ))
        if len(resp["roles"]) == 0:
            raise ValueError("Failed to assign roles to node")

        task = json.loads(self.client.post(
            "http://%s:8000/api/clusters/1/chef-config/" % host
        ))
        task_id = task['task_id']

        time.sleep(2)

        task = json.loads(self.client.get(
            "http://%s:8000/api/tasks/%s/" % (host, task_id)
        ))
        while True:
            try:
                self.check_tasks(task)
                break
            except StillPendingException:
                pass

        ret = self.exec_cmd("test -f /tmp/chef_success && echo 'SUCCESS'")
        if not "SUCCESS" in ret:
            raise Exception("Recipe failed to execute")

        self.disconnect()

    def check_tasks(self, task):
        if task['status'] != 'SUCCESS':
            if task['status'] == 'PENDING':
                raise StillPendingException("Task %s is still pending")
            raise Exception(
                "Task %s failed!\n %s" %
                (task['task_id'], str(task)),
            )
        if 'subtasks' in task and task['subtasks']:
            for subtask in task['subtasks']:
                self.check_tasks(subtask)