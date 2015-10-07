#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

# Because /var/lib/pgsql is mounted as a volume, reinstall if its files are
# missing
if rpm -V postgresql-server | grep -q missing; then
  yum reinstall -q -y postgresql-server
fi

puppet apply -v /etc/puppet/modules/nailgun/examples/postgres-only.pp


systemctl enable postgresql.service

#if [ -f '/etc/init.d/postgresql' ]; then
#  service postgresql stop
#  sudo -u postgres /usr/bin/postmaster -p 5432 -D /var/lib/pgsql/data
#else
#  pgver=$(rpm -q --queryformat '%{VERSION}' postgresql | cut -c'1-3')
#  service "postgresql-${pgver}" stop
#  sudo -u postgres "/usr/pgsql-${pgver}/bin/postmaster" -p 5432 -D "/var/lib/pgsql/${pgver}/data"
#fi
