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


# Run puppet to apply custom config
systemctl daemon-reload

puppet apply --debug --verbose --color false --detailed-exitcodes \
  --logdest /var/log/puppet/cobbler.log \
  /etc/puppet/modules/nailgun/examples/cobbler-only.pp || [[ $? == 2 ]]

puppet apply --debug --verbose --color false --detailed-exitcodes \
  --logdest /var/log/puppet/cobbler-dhcp-default-range.log \
  /etc/puppet/modules/nailgun/examples/dhcp-default-range.pp || [[ $? == 2 ]]


systemctl enable dnsmasq
systemctl restart dnsmasq
