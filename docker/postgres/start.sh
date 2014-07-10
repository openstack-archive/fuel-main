#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

puppet apply -v /etc/puppet/modules/nailgun/examples/postgres-only.pp

service postgresql stop

sudo -u postgres /usr/bin/postmaster -p 5432 -D /var/lib/pgsql/data
