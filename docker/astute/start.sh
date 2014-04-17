#!/bin/bash
puppet apply -v /etc/puppet/modules/nailgun/examples/astute-only.pp
pgrep supervisord >/dev/null && /usr/bin/supervisorctl shutdown
mkdir -p /var/log/astute
/usr/bin/supervisord -n
