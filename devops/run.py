
import time
import os

from devops.model import Environment, Node, Network, Interface
from devops.controller import Controller
from devops.driver.libvirt import Libvirt

from devops import yaml_config_loader

INSTALLATION_ISO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'install.iso'))
INSTALLATION_ISO_URL = "http://mc0n1-srt.srt.mirantis.net/nailgun-ubuntu-12.04-amd64.last.iso"

MASTER_AND_SLAVE_CONFIG = """
name: 'Sample environment'
networks:
  - network: internal
  - network: external
    type: bridged
nodes:
  - node: gateway
    disk: '5Gb'
    cdrom: '%s'
    networks: ['external', 'internal']
  - node: slug
    networks: ['internal']
""" % (INSTALLATION_ISO,)


def download_iso():
    if not os.path.exists(INSTALLATION_ISO):
        print("Downloading installation iso")
        os.system("wget -O '%s' -c '%s'" % (INSTALLATION_ISO, INSTALLATION_ISO_URL))
        print("Finished downloading installation iso")


def main():
    download_iso()

    environment = yaml_config_loader.load(MASTER_AND_SLAVE_CONFIG)

    external_network = environment.network['external']

    gateway = environment.node['gateway']
    gateway.vnc = True

    print("Creating environment")

    controller = Controller(Libvirt())
    controller.build_environment(environment)

    print("Environment created")

    print("Starting node")
    gateway.start()

    print("VNC is available on vnc://localhost:%d" % gateway.vnc_port)

    print("Waiting node to boot")
    time.sleep(15)

    print("Sending user input")

    ip = external_network.ip_addresses

    gateway.send_keys("""<Esc><Enter>
<Wait>
/install/vmlinuz initrd=/install/initrd.gz
 priority=critical
 locale=en_US
 file=/cdrom/preseed/manual.seed
 vga=788
 netcfg/get_ipaddress=%s
 netcfg/get_netmask=%s
 netcfg/get_gateway=%s
 netcfg/get_nameservers=%s
 netcfg/confirm_static=true
 <Enter>""" % (ip[2], ip.netmask, ip[1], ip[1]))
    print("Finished sending user input")

if __name__ == '__main__':
    main()

