#!/bin/bash

source /etc/env.vars

rm -rf /etc/yum.repos.d/*

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=http://$(route -n | awk '/^0.0.0.0/ {print $2}'):${DOCKER_PORT}/os/x86_64/
gpgcheck=0
EOF

yum clean expire-cache
yum update -y


puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/nailgun/examples/astute-only.pp || [[ $? == 2 ]]


cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all


chmod +x /usr/local/bin/start.sh

systemctl disable setup-container.service
