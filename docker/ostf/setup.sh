#!/bin/bash

source /etc/fuel/functions.sh
set -o errexit
trap 'print_debug_info' ERR
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

yum install -y --quiet python-fuelclient supervisor postgresql-libs

systemctl daemon-reload
puppet apply --color false --detailed-exitcodes --debug --verbose \
  /etc/puppet/modules/nailgun/examples/ostf-only.pp || [[ $? == 2 ]]

mkdir -p /etc/systemd/system/supervisord.service.d/
cat << EOF > /etc/systemd/system/supervisord.service.d/restart.conf
[Service]
Restart=always
RestartSec=5
FailureAction=reboot-force
EOF

systemctl set-default multi-user.target
systemctl enable supervisord.service

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all

systemctl enable start-container.service
