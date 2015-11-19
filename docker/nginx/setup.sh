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


mkdir -p /var/www/nailgun
chmod 755 /var/www/nailgun


systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  /etc/puppet/modules/nailgun/examples/nginx-only.pp || [[ $? == 2 ]]


mkdir -p /etc/systemd/system/nginx.service.d/
cat << EOF > /etc/systemd/system/nginx.service.d/restart.conf
[Service]
Restart=always
RestartSec=5
StartLimitAction=reboot-force
EOF

systemctl enable nginx.service


cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all


systemctl enable start-container.service
