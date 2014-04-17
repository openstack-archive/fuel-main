#!/bin/bash
mkdir -p /var/www/nailgun/dump
chmod -R 755 /var/www/nailgun
puppet apply -v /etc/puppet/modules/nailgun/examples/nginx-only.pp
nginx -g 'daemon off;'
