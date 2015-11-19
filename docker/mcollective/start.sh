#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb


puppet apply --debug --verbose --color false --detailed-exitcodes \
  /etc/puppet/modules/nailgun/examples/hiera-for-container.pp

# TODO(bpiotrowski): remove old file path after new ISO is used on CI
if [[ -f /etc/puppet/modules/mcollective/examples/mcollective-server-only.pp ]]; then
  puppet apply --debug --verbose --color false --detailed-exitcodes \
    /etc/puppet/modules/mcollective/examples/mcollective-server-only.pp
else
  puppet apply --debug --verbose --color false --detailed-exitcodes \
    /etc/puppet/modules/nailgun/examples/mcollective-only.pp
fi


for loopdev in $(seq 0 7); do
  mknod "/dev/loop${loopdev}" -m0660 b 7 ${loopdev} || :
done


#Stop daemon and restart it in the foreground
systemctl restart mcollective.service
