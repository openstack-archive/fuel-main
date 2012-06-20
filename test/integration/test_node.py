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

import paramiko

logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s', level=logging.DEBUG)

SOLO_PATH = os.path.join("..", "scripts", "agent")
DEPLOY_PATH = os.path.join("..", "bin", "deploy")
COOKBOOKS_PATH = os.path.join("..", "cookbooks")
SAMPLE_PATH = os.path.join("..", "scripts", "ci")
SAMPLE_REMOTE_PATH = "/home/ubuntu"


def read_until(channel, end, log=None):
    buff = ""
    while not buff.endswith(end):
        resp = channel.recv(9999)
        buff += resp
    if log:
        log.write(buff)
    return buff

# TODO: create helper
def copy_folder(sftp, local_path, remote_path):
    remote_root = os.path.join(
        remote_path,
        os.path.basename(local_path)
    )
    for root, dirs, fls in os.walk(local_path):
        rel = os.path.relpath(root, local_path)
        if rel == ".":
            curdir = remote_root
        else:
            curdir = os.path.join(remote_root, rel)
        sftp.mkdir(curdir)
        for fl in fls:
            sftp.put(
                os.path.join(root, fl),
                os.path.join(curdir, fl)
            )

def check_tasks(task):
    if task['status'] != 'SUCCESS':
        raise Exception("Task %s failed!\n %s" % 
                (task['task_id'], str(task)),
        )
    if 'subtasks' in task and task['subtasks']:
        for subtask in task['subtasks']:
            check_tasks(subtask)

# TODO: create basic class for implementing HTTP client in tests
class TestNode(TestCase):
    def test_node(self):
        # TODO: all in one ssh session
        host = str(ci.environment.node['admin'].ip_address)
        opener = urllib2.build_opener(urllib2.HTTPHandler)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username="ubuntu", password="r00tme")

        cookbook_remote_path = os.path.join(SAMPLE_REMOTE_PATH, "sample-cook")
        release_remote_path = os.path.join(SAMPLE_REMOTE_PATH, "sample-release.json")

        # removing old cookbooks
        (sin, sout, serr) = ssh.exec_command(
            "rm -rf %s" % cookbook_remote_path
        )
        (sin, sout, serr) = ssh.exec_command(
            "rm -rf %s" % os.path.join(SAMPLE_REMOTE_PATH, "cookbooks")
        )

        (sin, sout, serr) = ssh.exec_command(
            "rm -rf %s" % os.path.join(SAMPLE_REMOTE_PATH, "solo")
        )

        sftp = ssh.open_sftp()
        sftp.put(
            os.path.join(SAMPLE_PATH, "sample-release.json"),
            release_remote_path
        )

        sftp.mkdir(
            os.path.join(SAMPLE_REMOTE_PATH, "solo")
        )
        sftp.mkdir(
            os.path.join(SAMPLE_REMOTE_PATH, "solo/config")
        )

        sftp.put(
            DEPLOY_PATH,
            os.path.join(SAMPLE_REMOTE_PATH, "deploy")
        )
        sftp.put(
            os.path.join(SOLO_PATH, "solo.json"),
            os.path.join(SAMPLE_REMOTE_PATH, "solo", "config", "solo.json")
        )
        sftp.put(
            os.path.join(SOLO_PATH, "solo.rb"),
            os.path.join(SAMPLE_REMOTE_PATH, "solo", "config", "solo.rb")
        )

        copy_folder(sftp,
            os.path.join(SAMPLE_PATH, "sample-cook"),
            SAMPLE_REMOTE_PATH
        )
        copy_folder(sftp,
            COOKBOOKS_PATH,
            SAMPLE_REMOTE_PATH
        )

        sftp.close()

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

        chan = ssh.invoke_shell()

        chan.send("sudo -s\n")
        read_until(chan, "ubuntu: ")
        chan.send("r00tme\n")
        read_until(chan, "# ")

        for cmd in commands:
            print "~$ %s" % cmd
            chan.send(cmd+"\n")
            #with open("log.html", "a+") as l:
            #    read_until(chan, "# ", log=l)
            read_until(chan, "# ")

        req = urllib2.Request("http://%s:8000/api/clusters" % host,
                data='{ "name": "MyOwnPrivateCluster", "release": 1 }')
        req.add_header('Content-Type', 'application/json')
        resp = json.loads(opener.open(req).read())

        req = urllib2.Request("http://%s:8000/api/nodes" % host)
        nodes = json.loads(opener.open(req).read())
        if len(nodes) == 0:
            raise ValueError("Nodes list is empty")
        node_id = nodes[0]['id']

        req = urllib2.Request("http://%s:8000/api/clusters/1" % host,
                data='{ "nodes": ["%s"] }' % node_id)
        req.add_header('Content-Type', 'application/json')
        req.get_method = lambda: 'PUT'
        resp = json.loads(opener.open(req).read())

        req = urllib2.Request("http://%s:8000/api/clusters/1" % host)
        resp = json.loads(opener.open(req).read())
        if len(resp["nodes"]) == 0:
            raise ValueError("Failed to add node into cluster")

        req = urllib2.Request("http://%s:8000/api/nodes/%s" % (host, node_id),
            data='{ "roles": [1, 2] }'
        )
        req.add_header('Content-Type', 'application/json')
        req.get_method = lambda: 'PUT'
        resp = json.loads(opener.open(req).read())
        if len(resp["roles"]) == 0:
            raise ValueError("Failed to assign roles to node")

        req = urllib2.Request("http://%s:8000/api/clusters/1/chef-config/" % host,
            data="{}"
        )
        req.add_header('Content-Type', 'application/json')
        task_id = json.loads(opener.open(req).read())['task_id']
        time.sleep(2)

        req = urllib2.Request("http://%s:8000/api/tasks/%s/" % (host, task_id))
        resp = json.loads(opener.open(req).read())
        check_tasks(resp)

        chan.send("test -f /tmp/chef_success && echo 'SUCCESS'\n")
        ret = read_until(chan, "# ")
        if not "SUCCESS" in ret:
            raise Exception("Recipe failed to execute")

        ssh.close()
