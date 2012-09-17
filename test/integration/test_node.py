import os
import logging
import time
import json
import pprint
import posixpath
from devops.helpers import wait, tcp_ping, http
from integration import ci
from integration.base import Base
from helpers import SSHClient
from root import root

logging.basicConfig(format=':%(lineno)d: %(asctime)s %(message)s', level=logging.DEBUG)

AGENT_PATH = root("bin", "agent")
DEPLOY_PATH = root("bin", "deploy")
COOKBOOKS_PATH = root("cooks", "cookbooks")
SAMPLE_PATH = root("scripts", "ci")
SAMPLE_REMOTE_PATH = "/home/ubuntu"


class StillPendingException(Exception):
    pass


class TestNode(Base):
    def __init__(self, *args, **kwargs):
        super(TestNode, self).__init__(*args, **kwargs)
        self.remote = SSHClient()
        self.admin_host = None
        self.admin_user = "ubuntu"
        self.admin_passwd = "r00tme"
        self.slave_host = None
        self.slave_user = "root"
        self.slave_passwd = "r00tme"
        self.release_id = None

    def setUp(self):
        self.ip = self.get_admin_node_ip()
        self.admin_host = self.ip
        cookbook_remote_path = posixpath.join(SAMPLE_REMOTE_PATH, "sample-cook")
        mysql_remote_path = posixpath.join(COOKBOOKS_PATH, "mysql")
        release_remote_path = posixpath.join(SAMPLE_REMOTE_PATH, "sample-release.json")
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

        attempts = 0
        while True:
            releases = json.loads(self.client.get(
                    "http://%s:8000/api/releases/" % self.admin_host
                    ))

            for r in releases:
                logging.debug("Found release name: %s" % r["name"])
                if r["name"] == "Sample release":
                    logging.debug("Sample release id: %s" % r["id"])
                    self.release_id = r["id"]
                    break
                    
            if self.release_id:
                break

            if attempts >= 1:
                raise Exception("Release is not found")

            logging.error("Sample release is not found. Trying to upload")
            with self.remote.sudo:
                cmd = "/opt/nailgun/bin/create_release -f %s" % \
                    release_remote_path
                logging.info("Launching command: %s" % cmd)
                res = self.remote.execute(cmd)
                if res['exit_status']:
                    self.remote.disconnect()
                    raise Exception("Command failed: %s" % str(res))
                attempts += 1

#       todo install_cookbook always return 0
        commands = [
            "/opt/nailgun/bin/install_cookbook %s" % cookbook_remote_path
        ]
        with self.remote.sudo:
            for cmd in commands:
                logging.info("Launching command: %s" % cmd)
                res = self.remote.execute(cmd)
                logging.debug("Command result: %s" % pprint.pformat(res))
                if res['exit_status']:
                    self.remote.disconnect()
                    raise Exception("Command failed: %s" % str(res))

        self.remote.disconnect()

    def test_node_deploy(self):
        try:
            self.get_slave_id()
        except :
            pass
        timer = time.time()
        timeout = 600

        slave = ci.environment.node['slave']
        logging.info("Starting slave node")
        slave.start()

        while True:
            node = self.get_slave_node()
            if node is not None:
                logging.info("Node found")
                self.slave_host = node["ip"]
                self.slave_id = node["id"]
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
                data='{ "name": "MyOwnPrivateCluster", "release": %s }' % \
                    self.release_id, log=True
            )
            cluster = json.loads(cluster)

        resp = json.loads(self.client.put(
            "http://%s:8000/api/clusters/1" % self.admin_host,
            data='{ "nodes": ["%s"] }' % self.slave_id
        ))

        cluster = json.loads(self.client.get(
            "http://%s:8000/api/clusters/1" % self.admin_host
        ))
        if not len(cluster["nodes"]):
            raise ValueError("Failed to add node into cluster")

        roles_uploaded = json.loads(self.client.get(
            "http://%s:8000/api/roles?release_id=%s" % \
                (self.admin_host, self.release_id)
        ))

        """
        FIXME
        WILL BE CHANGED WHEN RENDERING WILL BE REWRITTEN
        """
        roles_ids = [
            role["id"] for role in roles_uploaded
        ]

        """
        resp = json.loads(self.client.put(
            "http://%s:8000/api/nodes/%s" % (self.admin_host, self.slave_id),
            data='{ "new_roles": %s, "redeployment_needed": true }' % str(roles_ids)
        ))
        if not len(resp["new_roles"]):
            raise ValueError("Failed to assign roles to node")
        """

        if node["status"] == "discover":
            logging.info("Node booted with bootstrap image.")
        elif node["status"] == "ready":
            logging.info("Node already installed.")
            self._slave_delete_test_file()

        logging.info("Provisioning...")
        changes = self.client.put(
            "http://%s:8000/api/clusters/1/changes/" % self.admin_host,
            log=True
        )
        print changes
        """
        task_id = task['task_id']
        logging.info("Task created: %s" % task_id)
        """
        logging.info("Waiting for completion of slave node software installation")
        timer = time.time()
        timeout = 1800
        while True:
            try:
                node = json.loads(self.client.get(
                    "http://%s:8000/api/nodes/%s" % (self.admin_host, self.slave_id)
                ))
                if not node["status"] == 'provisioning':
                    raise StillPendingException("Installation in progress...")
                elif node["status"] == 'error':
                    raise Exception(
                        "Installation failed!"
                    )
                elif node["status"] == 'ready':
                    logging.info("Installation complete!")
                    break
            except StillPendingException:
                if (time.time() - timer) > timeout:
                    raise Exception("Installation timeout expired!")
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
        if ret['exit_status']:
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

    def get_slave_node(self):
        response = self.client.get(
            "http://%s:8000/api/nodes/" % self.admin_host
        )
        nodes = json.loads(response)
        if nodes:
            return nodes[0]
