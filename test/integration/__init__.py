import os
import time
import tempfile

from devops.model import Environment, Network, Node, Disk, Cdrom, Interface
from devops.helpers import tcp_ping, wait
from helpers import SSHClient

import traceback
import logging
import devops

logger = logging.getLogger('integration')


class Ci(object):
    hostname = 'nailgun'
    domain = 'mirantis.com'
    installation_timeout = 1800
    deployment_timeout = 1800
    puppet_timeout = 1000

    def __init__(self, iso=None, forward='nat'):
        self.iso = iso
        self.environment = None
        self.forward = forward
        try:
            self.environment = devops.load('integration')
            logger.info("Successfully loaded existing environment")
        except Exception, e:
            logger.info(
                "Failed to load existing integration environment: %s",
                str(e)
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

            network = Network('default', forward=self.forward)
            environment.networks.append(network)

            node = Node('admin')
            node.memory = 1024
            node.vnc = True
            node.disks.append(
                Disk(size=30 * 1024 ** 3)
            )
            node.interfaces.append(Interface(network))
            node.cdrom = Cdrom(isopath=self.iso)
            node.boot = ['disk', 'cdrom']
            environment.nodes.append(node)

            for n in range(5):
                nodex = Node('slave%d' % (n + 1))
                nodex.memory = 768
                nodex.vnc = True
                nodex.disks.append(
                    Disk(size=30 * 1024 ** 3)
                )
                nodex.interfaces.append(Interface(network))
                nodex.boot = ['network']
                environment.nodes.append(nodex)

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
            'hostname': '.'.join((self.hostname, self.domain))
        }
        keys = """<Esc><Enter>
<Wait>
vmlinuz initrd=initrd.img ks=cdrom:/ks.cfg
 ip=%(ip)s
 netmask=%(mask)s
 gw=%(gw)s
 dns1=%(gw)s
 hostname=%(hostname)s
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

        logging.info("Waiting while bootstrapping is in progress")
        ssh = SSHClient()
        logpath = "/var/log/puppet/bootstrap_admin_node.log"
        str_success = "Finished catalog run"

        ssh.connect_ssh(
            str(self.environment.node['admin'].ip_address),
            "root",
            "r00tme"
        )
        wait(
            lambda: not ssh.execute(
                "grep '%s' '%s'" % (str_success, logpath)
            )['exit_status'],
            timeout=self.puppet_timeout
        )

        keyfiles = ssh.execute('ls -1 /root/.ssh/*rsa')['stdout']
        keyfiles = [os.path.join('/root/.ssh', name.strip())
                    for name in keyfiles]
        local_keyfiles = []
        node.metadata['keyfiles'] = local_keyfiles
        tempdir = tempfile.mkdtemp()
        for name in keyfiles:
            local_name = os.path.join(tempdir, os.path.basename(name))
            local_keyfiles.append(local_name)
            with open(local_name, 'w') as local_fd:
                fd = ssh.open(name)
                for line in fd:
                    local_fd.write(line)
                fd.close()
            os.chmod(local_name, 0600)
            logging.info("SSH keyfile %r saved." % local_name)
        ssh.disconnect()

        for node in self.environment.nodes:
            logging.info("Creating snapshot 'initial'")
            node.save_snapshot('initial')
            logging.info("Test node is ready at %s" % node.ip_address)

        devops.save(self.environment)
        logger.info("Admin node software is installed and ready for use")

        return True

    def destroy_environment(self):
        for name in self.environment.node['admin'].metadata['keyfiles']:
            try:
                os.unlink(name)
            except:
                pass
        try:
            os.rmdir(os.path.dirname(name))
        except:
            pass
        if self.environment:
            devops.destroy(self.environment)
        return True

ci = Ci()
