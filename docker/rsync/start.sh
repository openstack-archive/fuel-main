#!/bin/bash -e

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

puppet apply -v /etc/puppet/modules/nailgun/examples/puppetsync-only.pp
/usr/sbin/xinetd -dontfork
