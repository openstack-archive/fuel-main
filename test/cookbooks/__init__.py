import time, os
import devops
from devops.model import Environment, Network, Node, Disk, Cdrom, Interface
from devops.controller import Controller
from devops.driver.libvirt import Libvirt
from devops.helpers import tcp_ping, wait, TimeoutError
import traceback

import logging
logger = logging.getLogger('cookbooks')

class Ci:
    hostname = 'nailgun'
    domain = 'mirantis.com'

    def __init__(self, cache_file=None, iso=None):
        self.environment_cache_file = cache_file
        self.iso = iso
        self.environment = None
        qcow_file = cache_file + ".qcow2" if cache_file else "test-cookbooks.qcow2"
        self.image_path = os.path.join(os.path.dirname(__file__), qcow_file)
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

        if not self.iso:
            logger.critical("ISO path missing while trying to build cookbooks environment")
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

            # Creating qcow2 image to speed up the OS loading and not to put stuff on base ISO
            logger.info("Creating qcow2 image: %s" % self.image_path)
            os.system("qemu-img create -f qcow2 -b %s %s" % (self.iso, self.image_path))

            node.disks.append(Disk(path=self.image_path, format='qcow2'))
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

            devops.save(self.environment)

            try:
                os.makedirs(os.path.dirname(self.environment_cache_file))
            except OSError as e:
                logger.warning("Error occured while creating directory: %s", os.path.dirname(self.environment_cache_file))

            with file(self.environment_cache_file, 'w') as f:
                f.write(self.environment.id)

            logger.info("Environment has been saved")
            logger.info("Waiting test node installation software to boot")
            time.sleep(10)

            logger.info("Executing test node software installation")

            logger.info("Waiting ssh to respond...")
            wait(lambda: tcp_ping(node.ip_address, 22), timeout=1800)

            logger.info("Test node is ready at %s" % node.ip_address)

        except Exception, e:
            devops.save(self.environment)

            cache_file = self.environment_cache_file + '.candidate'
            try:
                os.makedirs(os.path.dirname(cache_file))
            except OSError:
                logger.warning("Exception occured while making directory: %s" % os.path.dirname(cache_file))
            with file(cache_file, 'w') as f:
                f.write(self.environment.id)
            logger.error("Failed to build environment. Candidate environment cache file is %s" % cache_file)
            return False

        return True

    def destroy_environment(self):
        if self.environment:
            devops.destroy(self.environment)

        if os.path.exists(self.image_path):
            os.remove(self.image_path)

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

