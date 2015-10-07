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

puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/puppetsync-only.pp || [[ $? == 2 ]]

systemctl mask xinetd.service
systemctl enable rsyncd.service

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all
