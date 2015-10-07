#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

#Workaround so nailgun can see version.yaml
ln -sf /etc/fuel/version.yaml /etc/nailgun/version.yaml
#Run puppet to apply custom config
puppet apply -v /etc/puppet/modules/nailgun/examples/nailgun-only.pp

#FIXME(dteselkin): for some f**ng reason /usr/share/nailgun/static
#                  is empty after puppet apply, despite the fact that
#                  package contains the files
#                  Reinstall package as a dirty workaround
yum -y --quiet reinstall fuel-nailgun
