#!/bin/bash

export PATH=${PATH}:/sbin:/usr/sbin

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

puppet apply -v /etc/puppet/modules/nailgun/examples/ostf-only.pp
service supervisord stop
/usr/bin/supervisord -n
