#!/bin/bash

puppet apply --logdest /var/log/puppet/firstboot.log --modulepath=/etc/puppet/modules /etc/puppet/modules/nailgun/examples/site.pp

# Run puppet second time (workaround for issue https://mirantis.jira.com/browse/PRD-109)
puppet apply --logdest /var/log/puppet/firstboot.log --modulepath=/etc/puppet/modules /etc/puppet/modules/nailgun/examples/site.pp

sed -i "/bootstrap_admin_node.sh/d" /etc/rc.local
