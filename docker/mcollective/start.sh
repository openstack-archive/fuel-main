#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

systemctl daemon-reload
puppet apply -d -v /etc/puppet/modules/mcollective/examples/mcollective-server-only.pp

#Stop daemon and restart it in the foreground
systemctl restart mcollective.service

