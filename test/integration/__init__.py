import time
from devops.model import Environment, Network, Node, Disk, Cdrom, Interface
from devops.controller import Controller
from devops.driver.libvirt import Libvirt
from devops.helpers import tcp_ping, wait

class Ci:
    def __init__(self):
        self.environment = Environment('test')

        self.default_network = Network('default')

        self.admin_node = Node('admin')
        self.admin_node.memory = 1024
        self.admin_node.vnc = True
        self.admin_node.cdrom = Cdrom(isopath='/var/www/local/nailgun-ubuntu-12.04-amd64.last.iso')
        self.admin_node.disks.append(Disk(size=30*1024**3))
        self.admin_node.interfaces.append(Interface(self.default_network))
        self.admin_node.boot = ['disk', 'cdrom']


        self.environment.networks.append(self.default_network)
        self.environment.nodes.append(self.admin_node)

        self.controller = Controller(Libvirt())
        self.controller.build_environment(self.environment)

        self.default_ip = self.default_network.ip_addresses


ci = Ci()

def setUp():
    ci.admin_node.start()
    time.sleep(10)
    ci.admin_node.send_keys("""<Esc><Enter>
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
""" % { 'ip': ci.default_ip[2], 'mask': ci.default_ip.netmask, 'gw': ci.default_ip[1] }) 

def tearDown():
    ci.controller.destroy_environment(ci.environment)
