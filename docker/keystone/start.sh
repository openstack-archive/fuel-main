#!/bin/bash -xe

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

puppet apply --detailed-exitcodes -v /etc/puppet/modules/nailgun/examples/keystone-only.pp || exitcode=$?
if [ $exitcode -ge 4 ]; then
  echo Puppet apply failed with exit code: $exitcode
  exit $exitcode
fi

service openstack-keystone stop
keystone-all
