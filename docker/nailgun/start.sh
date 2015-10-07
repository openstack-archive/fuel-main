#!/bin/bash

# Unprepared by 'start.sh' container doesn't have
# configuraion files in /etc/nailgun directory,
# and many services works incorrectly because if that.
# They just load system without any useful work done.
# So it's better to stop them now until 'puppet apply'.
supervisorctl stop all

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

#Workaround so nailgun can see version.yaml
ln -sf /etc/fuel/version.yaml /etc/nailgun/version.yaml

#Run puppet to apply custom config
puppet apply --debug --verbose --detailed-exitcodes /etc/puppet/modules/nailgun/examples/nailgun-only.pp
echo "Puppet exited with '$?'"

# Apply configuration changes from sysctl.conf
sysctl -f /etc/sysctl.conf

#FIXME(dteselkin): for some f**ng reason /usr/share/nailgun/static
#                  is empty after puppet apply, despite the fact that
#                  package contains the files
#                  Reinstall package as a dirty workaround
#UPDATE: It might be because this catalog is exported as a volume for
#        other containers, but it's just a guess.
yum -y --quiet reinstall fuel-nailgun

# (Re)start all services with updated configurations
supervisorctl reload

