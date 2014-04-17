#!/bin/bash
#link dump dir
rm -rf /var/www/nailgun/dump
ln -s /dump /var/www/nailgun/

puppet apply -d -v /etc/puppet/modules/mcollective/examples/mcollective-server-only.pp
sed -e 's/daemonize[[:space:]]*=[[:space:]]*1/daemonize = 0/g' -i /etc/mcollective/server.cfg
/usr/sbin/mcollectived --pid=/var/run/mcollectived.pid --config=/etc/mcollective/server.cfg

