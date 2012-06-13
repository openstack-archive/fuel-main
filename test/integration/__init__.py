import time
from devops.model import Environment, Network, Node, Disk, Cdrom, Interface
from devops.controller import Controller
from devops.driver.libvirt import Libvirt
from devops.helpers import tcp_ping, wait, TimeoutError

import logging
logger = logging.getLogger('integration.ci')

class Ci:

    envname = 'ci'
    iso = None
    
    def __init__(self):
        self.teardown = self.destroy
        self.controller = Controller(Libvirt())
        

    def env(self):
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
            wait(lambda: tcp_ping(self.environment.node['admin'].ip_address, 22), timeout=timeout)
        except TimeoutError as e:
            return False
        return True
        
    def admin_install(self):
        if not self.is_admin_installed(timeout=40):
            logger.info("Admin node is not installed. Trying to install.")
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
 netcfg/get_hostname=nailgun
 netcfg/get_domai=mirantis.com
 <Enter>
""" % { 'ip': self.environment.network['default'].ip_addresses[2], 
        'mask': self.environment.network['default'].ip_addresses.netmask, 
        'gw': self.environment.network['default'].ip_addresses[1] }) 

    def destroy(self):
        ens = self.controller.search_environments(self.envname)
        logger.debug("Found environments %s" % str(ens))
        for en in ens:
            logger.debug("Destroying %s" % en)
            env = self.controller.load_environment(en)
            self.controller.destroy_environment(env)

ci = None

def setUp():
    ci.environment.node['admin'].start()
    ci.admin_install()
    ci.is_admin_installed()

def tearDown():
    ci.teardown()
