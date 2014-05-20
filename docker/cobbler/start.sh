#!/bin/bash
mkdir -p /var/log/cobbler/{anamon,kicklog,syslog,tasks}

# reset authorized_keys file so puppet can a write new one
rm -f /etc/cobbler/authorized_keys

# Make sure services are not running (no pids, etc), puppet will
# configure and bring them up.
/etc/init.d/httpd stop
/etc/init.d/xinetd stop

# Run puppet to apply custom config
puppet apply -v /etc/puppet/modules/nailgun/examples/cobbler-only.pp
# Stop cobbler and dnsmasq
/etc/init.d/dnsmasq stop
/etc/init.d/cobblerd stop

# Running services
/etc/init.d/dnsmasq restart
cobblerd -F
