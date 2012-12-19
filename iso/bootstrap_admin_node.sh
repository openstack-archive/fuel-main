#!/bin/bash

puppet apply --modulepath=/opt/nailgun_puppet /opt/nailgun_puppet/nailgun/examples/site.pp 2>&1 | tee /var/log/puppet/firstboot.log
puppet apply -e 'class {puppetdb:}'
sed -i -e s/8080/8082/ /etc/puppetdb/conf.d/jetty.ini
puppet apply -e 'class {puppetdb::master::config: puppet_service_name=>"puppetmaster"}'

sed -i --follow-symlinks "/bootstrap_admin_node.sh/d" /etc/rc.local
