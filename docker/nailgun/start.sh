#!/bin/bash
#Workaround so nailgun can see version.yaml
ln -sf /etc/fuel/version.yaml /etc/nailgun/version.yaml
#Run puppet to apply custom config
puppet apply -v /etc/puppet/modules/nailgun/examples/nailgun-only.pp

/usr/bin/supervisord -n
