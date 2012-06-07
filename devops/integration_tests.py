import time
import os
import logging
import shutil


from devops.model import Environment, Network, Node, Disk, Cdrom, Interface
from devops.controller import Controller
from devops.network import IpNetworksPool
from devops.driver.libvirt import Libvirt
from devops.helpers import tcp_ping, wait

from devops import yaml_config_loader

ISO = "/var/www/local/nailgun-ubuntu-12.04-amd64.last.iso"


def log(message):
    print(message)



def main():

    environment = Environment('admin')
    
    network = Network('default')
    environment.networks.append(network)
    
    admin_node = Node('admin')
    admin_node.vnc = True
    admin_node.cdrom = Cdrom(isopath=ISO)
    admin_node.disks.append(Disk(size=30*1024**3))
    admin_node.interfaces.append(Interface(network))
    admin_node.boot += ['disk', 'cdrom']
    environment.nodes.append(admin_node)
    
    
    controller = Controller(Libvirt())
    controller.build_environment(environment)
    
    
    try:
        admin_node.start()
        time.sleep(10)
        ip = network.ip_addresses
        admin_node.send_keys("""<Esc><Enter>
<Wait>
/install/vmlinuz initrd=/install/initrd.gz
 priority=critical
 locale=en_US
 file=/cdrom/preseed/manual.seed
 vga=788
 netcfg/get_ipaddress=%(ipaddress)s
 netcfg/get_netmask=%(netmask)s
 netcfg/get_gateway=%(gateway)s
 netcfg/get_nameservers=%(gateway)s
 netcfg/confirm_static=true
 netcfg/get_hostname=nailgun
 netcfg/get_domai=mirantis.com
 <Enter>""" % { 'ipaddress': ip[2], 'netmask': ip.netmask, 'gateway': ip[1] })

        wait(lambda: tcp_ping(ip[2], 22))


        controller.destroy_environment(environment)
        
    except Exception as e:
        raise e

if __name__ == '__main__':
    main()
