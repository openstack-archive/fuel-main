#!/bin/bash
mkdir -p /var/log/cobbler/{anamon,kicklog,syslog,tasks}

#reset authorized_keys file so puppet can a write new one
rm -f /etc/cobbler/authorized_keys

#Run puppet to apply custom config
puppet apply -v /etc/puppet/modules/nailgun/examples/cobbler-only.pp
#stop cobbler and dnsmasq
/etc/init.d/dnsmasq stop
/etc/init.d/cobblerd stop

#Set up nailgun DB
/etc/init.d/httpd start
/etc/init.d/xinetd start
dnsmasq -d &
cobblerd -F
