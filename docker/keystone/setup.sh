#!/bin/bash

set -o errexit
set -o xtrace

rm -rf /etc/yum.repos.d/*

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=http://$(route -n | awk '/^0.0.0.0/ {print $2}'):${DOCKER_PORT}/os/x86_64/
gpgcheck=0
EOF

yum clean expire-cache
yum update -y

puppet apply --color false --detailed-exitcodes --debug --verbose \
  /etc/puppet/modules/nailgun/examples/keystone-only.pp || [[ $? == 2 ]]

mkdir -p /etc/systemd/system/openstack-keystone.service.d/
cat << EOF > /etc/systemd/system/openstack-keystone.service.d/restart.conf
[Service]
Restart=always
RestartSec=5
FailureAction=reboot-force
EOF

systemctl set-default multi-user.target
systemctl enable openstack-keystone.service

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all

systemctl enable start-container.service
