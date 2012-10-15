#!/bin/bash

puppet apply /tmp/site.pp

sed -i "/bootstrap_admin_node.sh/d" /etc/rc.local
