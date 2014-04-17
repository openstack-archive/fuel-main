#!/bin/bash
#Workaround so nailgun can see version.yaml
ln -sf /etc/fuel/version.yaml /etc/nailgun/version.yaml
#Run puppet to apply custom config
puppet apply -v /etc/puppet/modules/nailgun/examples/nailgun-only.pp

#Set up nailgun DB
/usr/bin/nailgun_syncdb
/usr/bin/nailgun_fixtures
/usr/bin/supervisord -n
