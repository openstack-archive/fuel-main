#!/bin/bash

mkdir -p /var/log/cobbler/{anamon,kicklog,syslog,tasks}

# Reset authorized_keys file so puppet can a write new one
rm -f /etc/cobbler/authorized_keys

# Run puppet to apply custom config
puppet apply -v /etc/puppet/modules/nailgun/examples/cobbler-only.pp

cat
