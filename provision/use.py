from provision.model import Profile, Node
import provision
import logging

logging.SimpleConfig()



pc = provision.ProvisionConfig()
pc.cn = "provision.driver.cobbler.Cobbler"
pc.url = "http://localhost/cobbler_api"
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
pf.save()


#nd = Node("node0")





