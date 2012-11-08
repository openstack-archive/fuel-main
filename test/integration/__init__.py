import os
import time

from devops.model import Environment, Network, Node, Disk, Cdrom, Interface
from devops.helpers import tcp_ping, wait
import traceback
import logging
import devops

logger = logging.getLogger('integration')


class Ci(object):
    hostname = 'nailgun'
    domain = 'mirantis.com'
    installation_timeout = 1800
    deployment_timeout = 1800

    def __init__(self, cache_file=None, iso=None):
        self.environment_cache_file = cache_file
        self.iso = iso
        self.environment = None
        self.nat = True
        try:
            self.environment = devops.load('integration')
            logger.info("Successfully loaded existing environment")
        except Exception, e:
            logger.info(
                "Failed to load existing integration environment: %s\n%s",
                str(e),
                traceback.format_exc()
            )
            pass

    def setup_environment(self):
        if self.environment:
            return True

        if not self.iso:
            logger.critical(
                "ISO path missing while trying "
                "to build integration environment"
            )
            return False

        logger.info("Building integration environment")

        try:
            environment = Environment('integration')

            network = Network('default')
            if not self.nat:
                network.forward = False
            environment.networks.append(network)

            node = Node('admin')
            node.memory = 2048
            node.vnc = True
            node.disks.append(
                Disk(size=30 * 1024 ** 3)
            )
            node.interfaces.append(Interface(network))
            node.cdrom = Cdrom(isopath=self.iso)
            node.boot = ['disk', 'cdrom']
            environment.nodes.append(node)

            node2 = Node('slave')
            node2.memory = 2048
            node2.vnc = True
            node2.disks.append(
                Disk(size=30 * 1024 ** 3)
            )
            node2.interfaces.append(Interface(network))
            node2.boot = ['network']
            environment.nodes.append(node2)

            devops.build(environment)
            self.environment = environment
        except Exception, e:
            logger.error(
                "Failed to build environment: %s\n%s",
                str(e),
                traceback.format_exc()
            )
            return False

        node.interfaces[0].ip_addresses = network.ip_addresses[2]
        devops.save(self.environment)
        logger.info("Environment has been saved")

        logger.info("Starting admin node")
        node.start()

        logger.info("Waiting admin node installation software to boot")
        #            todo await
        time.sleep(10)

        logger.info("Executing admin node software installation")
        params = {
            'ip': node.ip_address,
            'mask': network.ip_addresses.netmask,
            'gw': network.ip_addresses[1],
            'hostname': self.hostname,
            'domain': self.domain
        }
        keys = """<Esc><Enter>
<Wait>
vmlinuz initrd=initrd.img ks=cdrom:/ks.cfg
 ip=%(ip)s
 netmask=%(mask)s
 gw=%(gw)s
 dns1=%(gw)s
 hostname=%(hostname)s
 domain=%(domain)s
 <Enter>
""" % params
        node.send_keys(keys)

        logger.info(
            "Waiting for completion of admin node software installation"
        )
        wait(
            lambda: tcp_ping(node.ip_address, 22),
            timeout=self.installation_timeout
        )

        logger.info(
            "Got SSH access to admin node, "
            "waiting for ports 80 and 8000 to open"
        )
        wait(
            lambda: tcp_ping(node.ip_address, 80)
            and tcp_ping(node.ip_address, 8000),
            timeout=self.deployment_timeout
        )

        logger.info("Admin node software is installed and ready for use")

        return True

    def destroy_environment(self):
        if self.environment:
            devops.destroy(self.environment)
        return True

ci = Ci()
