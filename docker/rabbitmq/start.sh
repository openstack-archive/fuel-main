#!/bin/bash -xe

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

mkdir -p /var/log/rabbitmq
chown -R rabbitmq:rabbitmq /var/log/rabbitmq

exitcode=0
puppet apply --detailed-exitcodes -v /etc/puppet/modules/nailgun/examples/rabbitmq-only.pp || exitcode=$?
if [[ $exitcode != 0 && $exitcode != 2 ]]; then
  echo Puppet apply failed with exit code: $exitcode
  exit $exitcode
fi

set +e
systemctl stop rabbitmq-server.service
# Just in case stopping service fails
pkill -u rabbitmq

/usr/sbin/rabbitmq-server
