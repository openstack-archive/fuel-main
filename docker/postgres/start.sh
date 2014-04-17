#!/bin/bash
puppet apply -v /etc/puppet/modules/nailgun/examples/postgres-only.pp

service postgresql stop

sudo -u postgres /usr/bin/postmaster -p 5432 -D /var/lib/pgsql/data
