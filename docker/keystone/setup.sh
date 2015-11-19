#!/bin/bash -xe

rm -rf /etc/yum.repos.d/*

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=http://$(route -n | awk '/^0.0.0.0/ {print $2}'):${DOCKER_PORT}/os/x86_64/
gpgcheck=0
EOF

yum clean expire-cache
yum update -y

yum install -y  --quiet \
  os-client-config \
  python-tablib \
  python-unicodecsv \
  rubygem-thread_safe


systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  /etc/puppet/modules/nailgun/examples/keystone-only.pp || [[ $? == 2 ]]


mkdir -p /etc/systemd/system/openstack-keystone.service.d/
cat << EOF > /etc/systemd/system/openstack-keystone.service.d/restart.conf
[Service]
Restart=on-failure
RestartSec=5
EOF

systemctl enable openstack-keystone.service


cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all


systemctl enable start-container.service
