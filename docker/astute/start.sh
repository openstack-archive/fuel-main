#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

mkdir -p /var/log/astute


systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  --logdest /var/log/puppet/astute.log \
  /etc/puppet/modules/nailgun/examples/astute-only.pp
