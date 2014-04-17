#!/bin/bash -e
puppet apply -v /etc/puppet/modules/nailgun/examples/puppetsync-only.pp
/usr/sbin/xinetd -dontfork
