from provision.model.profile import Profile
from provision.model.node import Node
from provision.model.virtual_node import VirtualNode
import provision
import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


pc = provision.ProvisionConfig()
pc.cn = "provision.driver.cobbler.Cobbler"
pc.url = "http://10.100.0.2/cobbler_api"
pc.user = "cobbler"
pc.password = ""


pd = provision.ProvisionFactory.getInstance(pc)

pf = Profile("profile0")
pf.driver = pd
pf.arch = "x86_64"
pf.os = "ubuntu"
pf.osversion = "precise"
pf.kernel = "/var/www/cobbler/ks_mirror/precise-x86_64/linux"
pf.initrd = "/var/www/cobbler/ks_mirror/precise-x86_64/initrd.gz"
pf.seed = "/var/lib/mirror/preseed/precise.seed"
pf.kopts = ""
pf.save()

# nd = Node("node0")
# nd.driver = pd
# nd.mac = "52:54:00:31:95:3c"
# nd.profile = pf
# nd.kopts = ""
# nd.save()

vnd = VirtualNode("node1")
vnd.driver = pd
vnd.mac = "52:54:00:31:95:3c"
vnd.profile = pf
vnd.kopts = ""
vnd.save()
vnd.libvirtname = "cobbler_slave"
vnd.power_on()



