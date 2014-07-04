#!/bin/bash
chmod -R 755 /var/www/nailgun
chmod -R 755 /var/www/nailgun/* 2>/dev/null

puppet apply -v /etc/puppet/modules/nailgun/examples/nginx-only.pp
nginx -g 'daemon off;'
