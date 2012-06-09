default_conf = Cobbler.default_conf(node)

default["cobbler"]["updns"] = "8.8.8.8"
default["cobbler"]["next_server"] = default_conf[:next_server]
default["cobbler"]["server"] = default_conf[:server]
default["cobbler"]["bootstrap_kernel"] = "/var/lib/mirror/bootstrap/linux"
default["cobbler"]["bootstrap_initrd"] = "/var/lib/mirror/bootstrap/initrd.gz"
default["cobbler"]["bootstrap_ks_mirror_dir"] = "/var/www/cobbler/ks_mirror/bootstrap-precise-i386" 
default["cobbler"]["bootstrap_images_dir"] = "/var/www/cobbler/images/bootstrap-precise-i386" 
default["cobbler"]["dhcp_range"] = default_conf[:dhcp_range]
default["cobbler"]["gateway"] = default_conf[:gateway]
default["cobbler"]["pxetimeout"] = "20" #10=1sec
 
