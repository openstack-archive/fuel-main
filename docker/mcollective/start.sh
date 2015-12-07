#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

puppet apply --debug --verbose --color false --detailed-exitcodes \
  --logdest /var/log/puppet/mcollective-hiera.log \
  /etc/puppet/modules/nailgun/examples/hiera-for-container.pp

puppet apply --debug --verbose --color false --detailed-exitcodes \
  --logdest /var/log/puppet/mcollective.log \
  /etc/puppet/modules/nailgun/examples/mcollective-only.pp

for loopdev in $(seq 1 9); do
  mknod "/dev/loop${loopdev}" -m0660 b 7 ${loopdev} || :
done

#Stop daemon and restart it in the foreground
systemctl restart mcollective.service
