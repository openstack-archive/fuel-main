#!/usr/bin/env python

# vim: ts=4 sw=4
import os
import sys
import time
import shutil
from optparse import OptionParser

from devops.model import Environment, Network, Node, Disk, Cdrom, Interface
from devops.controller import Controller
from devops.network import IpNetworksPool
from devops.driver.libvirt import Libvirt
from devops.helpers import tcp_ping, wait

ADMIN_ISO_NAME = 'nailgun-ubuntu-12.04-amd64.last.iso'
ADMIN_ISO_URL = "http://mc0n1-srt.srt.mirantis.net/%s" % ADMIN_ISO_NAME
ADMIN_ISO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', ADMIN_ISO_NAME))

def log(message):
    print(message)

def download_iso():
    print("Downloading installation iso")
    os.system("cd '%s'; wget --timestamping '%s'" % (os.path.dirname(ADMIN_ISO_PATH), ADMIN_ISO_URL))
    print("Finished downloading installation iso")

def main():
    parser = OptionParser()
    (options, args) = parser.parse_args()

    if len(args) != 1:
        print("Usage: python install_admin.py <admin_disk_path>")
        sys.exit(1)

    admin_disk_path = args[0]

    download_iso()

    environment = Environment('admin')

    network = Network('default')
    environment.networks.append(network)

    admin_node = Node('admin')
    admin_node.vnc = True
    admin_node.cdrom = Cdrom(isopath=ADMIN_ISO_PATH)
    admin_node.disks.append(Disk(size=8*1024**3))
    admin_node.interfaces.append(Interface(network))
    admin_node.boot += ['disk', 'cdrom']
    environment.nodes.append(admin_node)

    log("Creating environment")

    controller = Controller(Libvirt())
    controller.build_environment(environment)

    log("Starting node")

    try:
        admin_node.start()

        log("Node started. VNC is available at port %d" % admin_node.vnc_port)

        log("Waiting node to boot")

        time.sleep(10)

        ip = network.ip_addresses

        log("Sending user input")

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
 <Enter>""" % { 'ipaddress': ip[2], 'netmask': ip.netmask, 'gateway': ip[1] })

        log("Waiting for node to install")

        wait(lambda: tcp_ping(ip[2], 22))

        log("Stopping node")

        admin_node.stop()

        log("Copying node's disk image")

        shutil.copy(admin_node.disks[0].path, admin_disk_path)

        print("Admin image creation completed. Image is stored at %s" % admin_disk_path)

        log("Destroying environment")
        controller.destroy_environment(environment)
    except:
        log("Error occurred, leaving environment for inspection")
        raise

if __name__ == '__main__':
    main()

