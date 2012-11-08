#!/bin/bash

puppet apply --modulepath=/etc/puppet/modules /etc/puppet/modules/nailgun/examples/site.pp 2>&1 | tee /var/log/puppet/firstboot.log

sed -i --follow-symlinks "/bootstrap_admin_node.sh/d" /etc/rc.local
