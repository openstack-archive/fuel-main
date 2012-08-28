import time, os

from devops.model import Environment, Network, Node, Disk, Cdrom, Interface
from devops.controller import Controller
from devops.driver.libvirt import Libvirt
from devops.helpers import tcp_ping, wait, TimeoutError
import traceback

import logging
import devops

logger = logging.getLogger('integration')

class Ci(object):
    hostname = 'nailgun'
    domain = 'mirantis.com'
    installation_timeout = 1800
    chef_timeout = 600

    def __init__(self, cache_file=None, iso=None):
        self.environment_cache_file = cache_file
        self.iso = iso
        self.environment = None
        if self.environment_cache_file and os.path.exists(self.environment_cache_file):
            logger.info("Loading existing integration environment...")
            with file(self.environment_cache_file) as f:
                environment_id = f.read()
            try:
                self.environment = devops.load(environment_id)
                logger.info("Successfully loaded existing environment")
            except Exception, e:
                logger.error("Failed to load existing integration environment: " + str(e) + "\n" + traceback.format_exc())
                pass

    def setup_environment(self):
        if self.environment:
            return True

        if not self.iso:
            logger.critical("ISO path missing while trying to build integration environment")
            return False

        logger.info("Building integration environment")

        try:
            environment = Environment('integration')

            network = Network('default')
            environment.networks.append(network)

            node = Node('admin')
            node.memory = 2048
            node.vnc = True
            node.disks.append(Disk(size=30*1024**3))
            node.interfaces.append(Interface(network))
            node.cdrom = Cdrom(isopath=self.iso)
            node.boot = ['disk', 'cdrom']
            environment.nodes.append(node)

            node2 = Node('slave')
            node2.memory = 2048
            node2.vnc = True
            node2.disks.append(Disk(size=30*1024**3))
            node2.interfaces.append(Interface(network))
            node2.boot = ['network']
            environment.nodes.append(node2)

            devops.build(environment)
        except Exception, e:
            logger.error("Failed to build environment: %s\n%s" % (str(e), traceback.format_exc()))
            return False

        self.environment = environment

        try:
            node.interfaces[0].ip_addresses = network.ip_addresses[2]

            logger.info("Starting admin node")
            node.start()

            logger.info("Waiting admin node installation software to boot")
            #            todo await
            time.sleep(10)

            logger.info("Executing admin node software installation")
            node.send_keys("""<Esc><Enter>
<Wait>
/install/vmlinuz initrd=/install/initrd.gz
 priority=critical
 locale=en_US
 file=/cdrom/preseed/manual.seed
 vga=788
 netcfg/get_ipaddress=%(ip)s
 netcfg/get_netmask=%(mask)s
 netcfg/get_gateway=%(gw)s
 netcfg/get_nameservers=%(gw)s
 netcfg/confirm_static=true
 netcfg/get_hostname=%(hostname)s
 netcfg/get_domai=%(domain)s
 <Enter>
""" % { 'ip': node.ip_address,
        'mask': network.ip_addresses.netmask,
        'gw': network.ip_addresses[1],
        'hostname': self.hostname,
        'domain': self.domain})

            logger.info("Waiting for completion of admin node software installation")
            wait(lambda: tcp_ping(node.ip_address, 22), timeout=self.installation_timeout)

            logger.info("Got SSH access to admin node, waiting for ports 80 and 8000 to open")
            wait(lambda: tcp_ping(node.ip_address, 80) and tcp_ping(node.ip_address, 8000), timeout=self.chef_timeout)

            logger.info("Admin node software is installed and ready for use")

            devops.save(self.environment)

            try:
                os.makedirs(os.path.dirname(self.environment_cache_file))
            except OSError as e:
                logger.warning("Error occured while creating directory: %s", os.path.dirname(self.environment_cache_file))

            with file(self.environment_cache_file, 'w') as f:
                f.write(self.environment.id)

            logger.info("Environment has been saved")
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

        if self.environment_cache_file and os.path.exists(self.environment_cache_file):
            os.remove(self.environment_cache_file)

        return True

ci = None

def setUp():
    if not ci.setup_environment():
        raise Exception, "Failed to setup integration environment"

def tearDown():
    if not ci.environment_cache_file:
        ci.destroy_environment()

