#!/bin/bash -xe

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb


systemctl daemon-reload

puppet apply --debug --verbose --color false --detailed-exitcodes \
  --logdest /var/log/puppet/keystone.log \
  /etc/puppet/modules/nailgun/examples/keystone-only.pp || [[ $? == 2 ]]

puppet apply --detailed-exitcodes -v /etc/puppet/modules/nailgun/examples/keystone-token-disable.pp || exitcode=$?
if [[ $exitcode != 0 && $exitcode != 2 ]]; then
  echo Puppet apply failed with exit code: $exitcode
  exit $exitcode
fi
