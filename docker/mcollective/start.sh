#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

puppet apply -d -v /etc/puppet/modules/mcollective/examples/mcollective-server-only.pp
sed -e 's/daemonize[[:space:]]*=[[:space:]]*1/daemonize = 0/g' -i /etc/mcollective/server.cfg
/usr/sbin/mcollectived --pid=/var/run/mcollectived.pid --config=/etc/mcollective/server.cfg

