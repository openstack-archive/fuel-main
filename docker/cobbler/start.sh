#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

mkdir -p /var/log/cobbler/{anamon,kicklog,syslog,tasks}

# reset authorized_keys file so puppet can a write new one
rm -f /etc/cobbler/authorized_keys

# Because /var/lib/cobbler is mounted as a volume, reinstall if its files are
# missing
if rpm -V cobbler | grep -q missing; then
  yum reinstall -q -y cobbler
fi
if rpm -V cobbler-web | grep -q missing; then
  yum reinstall -q -y cobbler-web
fi

# Make sure services are not running (no pids, etc), puppet will
# configure and bring them up.
/etc/init.d/httpd stop
/etc/init.d/xinetd stop

# Run puppet to apply custom config
puppet apply -v /etc/puppet/modules/nailgun/examples/cobbler-only.pp
# Stop cobbler and dnsmasq
/etc/init.d/dnsmasq stop
/etc/init.d/cobblerd stop

# Check if we have any dhcp-ranges configured in dnsmasq. If not, then
# we need to create default dhcp-range for fuelweb_admin network that
# was configured via fuelmenu and stored in /etc/fuel/astute.yaml
ls /etc/dnsmasq.d/*.conf || \
  puppet apply -d -v /etc/puppet/modules/nailgun/examples/dhcp-default-range.pp

# Running services
/etc/init.d/dnsmasq restart
cobblerd -F
