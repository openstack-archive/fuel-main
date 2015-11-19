#!/bin/bash -xe

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb


mkdir -p /var/log/rabbitmq
chown -R rabbitmq:rabbitmq /var/log/rabbitmq


systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  /etc/puppet/modules/nailgun/examples/rabbitmq-only.pp || [[ $? == 2 ]]


systemctl stop rabbitmq-server.service
# Just in case stopping service fails
pkill -u rabbitmq

systemctl start rabbitmq-server.service
