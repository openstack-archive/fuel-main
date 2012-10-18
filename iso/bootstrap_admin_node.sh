#!/bin/bash

puppet apply --modulepath=/etc/puppet/modules /etc/puppet/modules/nailgun/examples/site.pp

sed -i "/bootstrap_admin_node.sh/d" /etc/rc.local
