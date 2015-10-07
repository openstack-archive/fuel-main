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

mkdir -p /opt/gateone/users/ANONYMOUS/ /var/log/nailgun

mkdir -p /root/.ssh
chmod 700 /root/.ssh
touch /root/.ssh/id_rsa.pub
chmod 600 /root/.ssh/id_rsa.pub

puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/nailgun-only.pp || [[ $? == 2 ]]

mkdir -p /var/log/remote /var/www/nailgun

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all

systemctl enable start-container.service
