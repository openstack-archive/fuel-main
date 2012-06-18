import time
from devops.model import Environment, Network, Node, Disk, Cdrom, Interface
from devops.controller import Controller
from devops.driver.libvirt import Libvirt
from devops.helpers import tcp_ping, wait, TimeoutError

import logging
logger = logging.getLogger('integration.ci')

class Ci:

    envname = 'ci'
    hostname = 'nailgun'
    domain = 'mirantis.com'
    iso = None
    
    def __init__(self):
        self.controller = Controller(Libvirt())
        
    def setUp(self):
        logger.debug("Preparing devops environment")
        self.devops_env()
        logger.debug("Starting admin node")
        self.environment.node['admin'].start()
        if not self.is_admin_installed(timeout=30):
            logger.debug("Admin node seems not installed")
            self.admin_install()
        logger.info("Waiting for completion of admin node installation")
        self.is_admin_installed()
        logger.info("Admin node seems installed")

    def tearDown(self):
        logger.debug("Destroying devops environment")
        self.destroy()

    def devops_env(self):
        found = self.controller.search_environments(self.envname)
        if found:
            environment = self.controller.load_environment(found[0])
        else:
            environment = Environment(self.envname)
            
            network = Network('default')
            environment.networks.append(network)
            
            node = Node('admin')
            node.memory = 2048
            node.vnc = True
            node.disks.append(Disk(size=30*1024**3))
            node.interfaces.append(Interface(network))
            if self.iso:
                node.cdrom = Cdrom(isopath=self.iso)
            node.boot = ['disk', 'cdrom']
            environment.nodes.append(node)
        
            self.controller.build_environment(environment)
            self.controller.save_environment(environment)

        self.environment = environment

    def is_admin_installed(self, timeout=None):
        try:
            logger.info("Checking if admin node already installed")
            admin_node = self.environment.node['admin']
            wait(lambda: logger.info("Node IP address is %s", admin_node.ip_address) or tcp_ping(admin_node.ip_address, 22), timeout=timeout)
        except TimeoutError as e:
            return False
        return True
        
    def admin_install(self):
        logger.info("Installing admin node.")
        logger.info("Sending keys to install admin node.")
        self.environment.node['admin'].send_keys("""<Esc><Enter>
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
""" % { 'ip': self.environment.network['default'].ip_addresses[2], 
        'mask': self.environment.network['default'].ip_addresses.netmask, 
        'gw': self.environment.network['default'].ip_addresses[1],
        'hostname': self.hostname,
        'domain': self.domain}) 

    def destroy(self):
        ens = self.controller.search_environments(self.envname)
        logger.debug("Found environments %s" % str(ens))
        for en in ens:
            logger.debug("Destroying %s" % en)
            env = self.controller.load_environment(en)
            self.controller.destroy_environment(env)


ci = None

def setUp():
    ci.setUp()

def tearDown():
    ci.tearDown()
