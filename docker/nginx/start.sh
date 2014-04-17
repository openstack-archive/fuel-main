#!/bin/bash
#link dump dir
rm -rf /var/www/nailgun/dump
ln -s /dump /var/www/nailgun/

chmod -R 755 /var/www/nailgun
puppet apply -v /etc/puppet/modules/nailgun/examples/nginx-only.pp
nginx -g 'daemon off;'
