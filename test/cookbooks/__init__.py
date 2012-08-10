import time, os
import devops
import unittest
from devops.model import Environment, Network, Node, Disk, Cdrom, Interface
from devops.controller import Controller
from devops.driver.libvirt import Libvirt
from devops.helpers import tcp_ping, wait, TimeoutError, ssh, http_server
import traceback

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
                self.node = self.environment.nodes[0]
                self.network = self.environment.networks[0]
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
        self.node = node
        self.network = network

        try:
            logger.info("Starting test node")
            node.start()

            logger.info("Waiting ssh to respond...")
            wait(lambda: tcp_ping(node.ip_address, 22), timeout=1800)

            logger.info("Setting up repository configuration")

            remote = ssh(node.ip_address, username='root', password='r00tme')
            repo = remote.open('/etc/yum.repos.d/mirantis.repo', 'w')
            repo.write("""
[mirantis]
name=Mirantis repository
baseurl=http://%s:8000
enabled=1
gpgcheck=0
            """ % network.ip_addresses[1])
            repo.close()

            remote.execute('yum makecache')

            logger.info("Disabling firewall")

            remote.execute('service iptables save')
            remote.execute('service iptables stop')
            remote.execute('chkconfig iptables off')

            logger.info("Creating snapshot 'blank'")

            node.save_snapshot('empty')

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

    def setup_repository(self):
        remote = ssh(self.node.ip_address, username='root', password='r00tme')
        repo = remote.open('/etc/yum.repos.d/mirantis.repo', 'w')
        repo.write("""
[mirantis]
name=Mirantis repository
baseurl=http://%s:%d
enabled=1
gpgcheck=0
        """ % (self.network.ip_addresses[1], self.repository_server.port))
        repo.close()

        remote.execute('yum makecache')


    def start_environment(self):
        self.repository_server = http_server(
            os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "..", "..",
                    "build", "packages", "centos", "Packages"
                ) 
            )
        )

        self.setup_repository()

        self.node.save_snapshot('blank', force=True)

        return True

    def shutdown_environment(self):
        if hasattr(self, 'repository_server'):
            self.repository_server.stop()

        return True

ci = None

def setUp():
    if not ci.setup_environment():
        raise Exception, "Failed to setup cookbooks environment"
    if not ci.start_environment():
        raise Exception, "Failed to run cookboks environment"

def tearDown():
    ci.shutdown_environment()
    if not ci.environment_cache_file:
        ci.destroy_environment()

class CookbookTestCase(unittest.TestCase):
    cookbooks = []
    cookbooks_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..", "..", "cooks", "cookbooks"
        ) 
    )

    @classmethod
    def setUpState(klass):
        pass

    @classmethod
    def setUpClass(klass):
        klass.node = ci.environment.node['cookbooks']
        klass.ip = klass.node.ip_address

        klass.remote = ssh(klass.ip, username='root', password='r00tme')

        snapshot = klass.__name__

        if not os.environ.get('DEVELOPMENT') or not snapshot in klass.node.snapshots:
            logger.info('Setting up state for %s' % klass.__name__)

            if snapshot in klass.node.snapshots:
                klass.node.delete_snapshot(snapshot)

            klass.node.restore_snapshot('blank')
            klass.remote.reconnect()

            klass.upload_cookbooks(klass.cookbooks)
            klass.setUpState()

            klass.node.save_snapshot(snapshot)

            logger.info('Finished state for %s' % klass.__name__)

    @classmethod
    def upload_cookbooks(klass, cookbooks):
        klass.remote.mkdir("/opt/os-cookbooks/")

        solo_rb = klass.remote.open('/tmp/solo.rb', 'w')
        solo_rb.write("""
file_cache_path "/tmp/chef"
cookbook_path "/opt/os-cookbooks"
        """)
        solo_rb.close()

        for cookbook in cookbooks:
            klass.remote.upload(os.path.join(klass.cookbooks_dir, cookbook), "/opt/os-cookbooks/")

    @classmethod
    def chef_solo(klass, attributes={}):
        ci.setup_repository()

        recipes = attributes.get('recipes') or attributes.get('run_list')
        logger.info('Running Chef with recipes: %s' % (', '.join(recipes)))

        solo_json = klass.remote.open('/tmp/solo.json', 'w')
        solo_json.write(json.dumps(attributes))
        solo_json.close()

        result = klass.remote.execute("chef-solo -l debug -c /tmp/solo.rb -j /tmp/solo.json")
        if result['exit_code'] != 0:
            stdout = result['stdout']
            stderr = result['stderr']

            while stdout[-1] == '':
                stdout.pop()

            logger.error(''.join(stdout))

            raise ChefRunError(result['exit_code'], stdout[-1], ''.join(stderr))

        logger.info('Chef run successfully finished')

        return result

    @classmethod
    def chef_run_recipe(klass, recipe):
        klass.remote.mkdir('/opt/os-cookbooks/test')
        klass.remote.mkdir('/opt/os-cookbooks/test/recipes')

        default_rb = klass.remote.open('/opt/os-cookbooks/test/recipes/default.rb', 'w')
        default_rb.write(recipe)
        default_rb.close()

        klass.chef_solo({'recipes': ['test']})

    def setUp(self):
        self.node.restore_snapshot(self.__class__.__name__)
        self.remote.reconnect()

