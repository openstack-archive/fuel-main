#!/bin/bash
puppet apply -v /etc/puppet/modules/nailgun/examples/keystone-only.pp
service openstack-keystone stop
keystone-all
