#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

mkdir -p /var/log/rabbitmq
chown -R rabbitmq:rabbitmq /var/log/rabbitmq

puppet apply -v /etc/puppet/modules/nailgun/examples/rabbitmq-only.pp

service rabbitmq-server stop
#Just in case stopping service fails
pkill -u rabbitmq

/usr/sbin/rabbitmq-server
