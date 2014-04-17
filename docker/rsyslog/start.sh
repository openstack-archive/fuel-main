#!/bin/bash

puppet apply -d -v /etc/puppet/modules/nailgun/examples/rsyslog-only.pp

/sbin/rsyslogd -i /var/run/syslogd.pid -c 5 -x -n

