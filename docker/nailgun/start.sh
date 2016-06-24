#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb


#Workaround so nailgun can see version.yaml
ln -sf /etc/fuel/version.yaml /etc/nailgun/version.yaml


#Run puppet to apply custom config
systemctl daemon-reload

puppet apply --debug --verbose --color false --detailed-exitcodes \
  --logdest /var/log/puppet/nailgun.log \
  /etc/puppet/modules/nailgun/examples/nailgun-only.pp

systemctl restart supervisord.service
