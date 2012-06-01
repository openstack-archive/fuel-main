
import time
import os

from devops.model import Environment, Node, Network, Interface
from devops.controller import Controller
from devops.driver.libvirt import Libvirt

from devops import yaml_config_loader

INSTALLATION_ISO = "/var/tmp/nailgun-ubuntu-12.04-amd64.last.iso"
INSTALLATION_ISO_URL = "http://mc0n1-srt.srt.mirantis.net/nailgun-ubuntu-12.04-amd64.last.iso"

if not os.path.exists(INSTALLATION_ISO):
    print("Downloading installation iso")
    os.system("wget -O '%s' -c '%s'" % (INSTALLATION_ISO, INSTALLATION_ISO_URL))
    print("Finished downloading installation iso")

env = yaml_config_loader.load("""
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
""" % (INSTALLATION_ISO,))

gateway = env.node['gateway']
gateway.vnc = True

print("Creating environment")

controller = Controller(Libvirt())
controller.build_environment(env)

print("Environment created")

print("Starting node")
gateway.start()
print("Waiting node to boot")
time.sleep(10)
print("Sending user input")
gateway.send_keys("""<Esc><Enter>
<Wait>
/install/vmlinuz initrd=/install/initrd.gz
 priority=critical
 locale=en_US
 file=/cdrom/preseed/manual.seed
 vga=788
 netcfg/get_ipaddress=10.20.0.2
 netcfg/get_netmask=255.255.255.0
 netcfg/get_gateway=10.20.0.1
 netcfg/get_nameservers=10.20.0.1
 netcfg/confirm_static=true
 netcfg/get_hostname=nailgun
 netcfg/get_domai=mirantis.com
 <Enter>
""")
print("Finished sending user input")

# print("Sleeping 5 seconds")
# time.sleep(5)
# 
# controller.destroy_environment(env)
# 
# print("Environment destroyed")

