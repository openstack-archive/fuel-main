import time, os
import devops
import unittest
from devops.model import Environment, Network, Node, Disk, Cdrom, Interface
from devops.controller import Controller
from devops.driver.libvirt import Libvirt
from devops.helpers import tcp_ping, wait, TimeoutError
import traceback

from integration.helpers import HTTPClient, SSHClient
import simplejson as json

import logging
logger = logging.getLogger('cookbooks')

class ChefRunError(Exception):
    pass

class Ci:
    hostname = 'nailgun'
    domain = 'mirantis.com'

    def __init__(self, cache_file=None, base_image=None):
        self.environment_cache_file = cache_file
        self.base_image = base_image
        self.environment = None
        if self.environment_cache_file and os.path.exists(self.environment_cache_file):
            logger.info("Loading existing cookbooks environment...")
            with file(self.environment_cache_file) as f:
                environment_id = f.read()

            try:
                self.environment = devops.load(environment_id)
                logger.info("Successfully loaded existing environment")
            except Exception, e:
                logger.error("Failed to load existing cookbooks environment: " + str(e) + "\n" + traceback.format_exc())
                pass

    def setup_environment(self):
        if self.environment:
            return True

        if not self.base_image:
            logger.critical("Base image path is missing while trying to build cookbooks environment")
            return False

        logger.info("Building cookbooks environment")

        try:
            environment = Environment('cookbooks')

            network = Network(name='default', dhcp_server=True)
            environment.networks.append(network)

            node = Node('cookbooks')
            node.memory = 1024
            node.vnc = True
            node.interfaces.append(Interface(network))
            node.disks.append(Disk(base_image=self.base_image, format='qcow2'))
            node.boot = ['disk']
            environment.nodes.append(node)

            devops.build(environment)
        except Exception, e:
            logger.error("Failed to build environment: %s\n%s" % (str(e), traceback.format_exc()))
            return False

        self.environment = environment

        try:
            logger.info("Starting test node")
            node.start()

            logger.info("Waiting ssh to respond...")
            wait(lambda: tcp_ping(node.ip_address, 22), timeout=1800)

            logger.info("Setting up repository configuration")

            remote = SSHClient()
            remote.connect_ssh(str(node.ip_address), "root", "r00tme")
            repo = remote.open('/etc/yum.repos.d/mirantis.repo', 'w')
            repo.write("""
[mirantis]
name=Mirantis repository
baseurl=http://twin0d.srt.mirantis.net/centos62
enabled=1
gpgcheck=0
            """)
            repo.close()

            logger.info("Disabling firewall")

            remote.execute('service iptables save')
            remote.execute('service iptables stop')
            remote.execute('chkconfig iptables off')

            logger.info("Test node is ready at %s" % node.ip_address)

            devops.save(self.environment)
            if not os.path.exists(os.path.dirname(self.environment_cache_file)):
                os.makedirs(os.path.dirname(self.environment_cache_file))

            with file(self.environment_cache_file, 'w') as f:
                f.write(self.environment.id)

            logger.info("Environment has been saved")

        except Exception, e:
            logger.error("Exception during environment setup: %s" % str(e))

            devops.save(self.environment)

            cache_file = self.environment_cache_file + '.candidate'
            if not os.path.exists(os.path.dirname(cache_file)):
                os.makedirs(os.path.dirname(cache_file))

            with file(cache_file, 'w') as f:
                f.write(self.environment.id)

            logger.error("Failed to build environment. Candidate environment cache file is %s" % cache_file)
            return False

        return True

    def destroy_environment(self):
        if self.environment:
            devops.destroy(self.environment)

        if self.environment_cache_file and os.path.exists(self.environment_cache_file):
            os.remove(self.environment_cache_file)

        return True


ci = None

def setUp():
    if not ci.setup_environment():
        raise Exception, "Failed to setup cookbooks environment"

def tearDown():
    if not ci.environment_cache_file:
        ci.destroy_environment()

class CookbookTestCase(unittest.TestCase):
    cookbooks = []

    def setUp(self):
        self.ip = ci.environment.node['cookbooks'].ip_address
        self.cookbooks_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..", "..", "cooks", "cookbooks"
            ) 
        )

        self.remote = SSHClient()
        self.remote.connect_ssh(str(self.ip), "root", "r00tme")
        self.remote.mkdir("/opt/os-cookbooks/")

        solo_rb = self.remote.open('/tmp/solo.rb', 'w')
        solo_rb.write("""
file_cache_path "/tmp/chef"
cookbook_path "/opt/os-cookbooks"
        """)
        solo_rb.close()

        for cookbook in self.cookbooks:
            self.remote.scp_d(os.path.join(self.cookbooks_dir, cookbook), "/opt/os-cookbooks/")

    def chef_solo(self, attributes={}):
        solo_json = self.remote.open('/tmp/solo.json', 'w')
        solo_json.write(json.dumps(attributes))
        solo_json.close()

        result = self.remote.execute("chef-solo -l debug -c /tmp/solo.rb -j /tmp/solo.json")
        if result['exit_status'] != 0:
            stdout = result['stdout']
            stderr = result['stderr']

            while stdout[-1] == '':
                stdout.pop()

            logger.error(''.join(stdout))

            raise ChefRunError(result['exit_status'], stdout[-1], ''.join(stderr))

        return result

