#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb


puppet apply --debug --verbose \
    /etc/puppet/modules/nailgun/examples/hiera-for-container.pp


sed -e 's/daemonize[[:space:]]*=[[:space:]]*1/daemonize = 0/g' -i /etc/mcollective/server.cfg
puppet apply --debug --verbose \
    /etc/puppet/modules/mcollective/examples/mcollective-server-only.pp


# Create loop devices if needed for IBP to setup image
for loopdev in $(seq 1 9); do
    mknod "/dev/loop${loopdev}" -m0660 b 7 ${loopdev} ||:
done

