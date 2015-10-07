#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

mkdir -p /var/log/astute

systemctl daemon-reload
puppet apply -v /etc/puppet/modules/nailgun/examples/astute-only.pp

for loopdev in $(seq 0 7); do
  mknod "/dev/loop${loopdev}" -m0660 b 7 ${loopdev} || :
done
