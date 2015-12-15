#!/bin/bash -xe

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb


mkdir -p /var/log/rabbitmq
chown -R rabbitmq:rabbitmq /var/log/rabbitmq


systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  --logdest /var/log/puppet/rabbitmq.log \
  /etc/puppet/modules/nailgun/examples/rabbitmq-only.pp || [[ $? == 2 ]]
