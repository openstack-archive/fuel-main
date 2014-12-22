#!/bin/bash -xe

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

exitcode=0
puppet apply --detailed-exitcodes -v /etc/puppet/modules/nailgun/examples/keystone-only.pp || exitcode=$?
if [[ $exitcode != 0 && $exitcode != 2 ]]; then
  echo Puppet apply failed with exit code: $exitcode
  exit $exitcode
fi

service openstack-keystone stop
sed -i -e 's/^public_bind_host=.*$/public_bind_host=0.0.0.0/g' -e 's/^admin_bind_host=.*$/admin_bind_host=0.0.0.0/g' /etc/keystone/keystone.conf
keystone-all
