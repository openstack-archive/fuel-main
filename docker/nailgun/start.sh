#!/bin/bash

ln -s /etc/fuel/nailgun/version.yaml /etc/nailgun/version.yaml || true
puppet apply -v -d /etc/puppet/modules/nailgun/examples/nailgun-only.pp

/usr/bin//nailgun_syncdb
/usr/bin/nailgun_fixtures

pgrep supervisord && /etc/init.d/supervisord stop

/usr/bin/supervisord -n

