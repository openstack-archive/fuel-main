#!/bin/sh

umask 0177
cp /etc/fuel/astute.yaml /etc/fuel/astute.yaml.bak
dockerctl shell cobbler cat /etc/cobbler/dnsmasq.template | python /var/www/nailgun/docker/utils/extra_nets_from_cobbler.py > /etc/fuel/astute.yaml.tmp
mv /etc/fuel/astute.yaml.tmp /etc/fuel/astute.yaml
