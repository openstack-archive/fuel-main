#!/bin/bash
puppet apply -v /etc/puppet/modules/nailgun/examples/ostf-only.pp
/usr/bin/supervisord -n
