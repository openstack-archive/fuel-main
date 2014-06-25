#!/bin/bash
#link dump dir
rm -rf /var/www/nailgun/dump
ln -s /dump /var/www/nailgun/

find /var/www/nailgun -follow -exec chmod 755 {} \;
puppet apply -v /etc/puppet/modules/nailgun/examples/nginx-only.pp
nginx -g 'daemon off;'
