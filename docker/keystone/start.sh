#!/bin/bash -xe

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

systemctl daemon-reload
puppet apply --detailed-exitcodes -v /etc/puppet/modules/nailgun/examples/keystone-only.pp || [[ $? == 2 ]]
