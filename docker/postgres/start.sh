#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb


# Because /var/lib/pgsql is mounted as a volume,
# reinstall if its files are missing
if rpm -V postgresql-server | grep -q missing; then
  yum reinstall -q -y postgresql-server
fi


systemctl daemon-reload

puppet apply --debug --verbose --color false --detailed-exitcodes \
  --logdest /var/log/puppet/postgres.log \
  /etc/puppet/modules/nailgun/examples/postgres-only.pp


systemctl enable postgresql.service
