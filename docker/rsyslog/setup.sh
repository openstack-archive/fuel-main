#!/bin/bash -xe

rm -rf /etc/yum.repos.d/*

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=http://$(route -n | awk '/^0.0.0.0/ {print $2}'):${DOCKER_PORT}/repo/os/x86_64/
gpgcheck=0

[mos]
name=MOS Local Repo
baseurl=http://$(route -n | awk '/^0.0.0.0/ {print $2}'):${DOCKER_PORT}/mos-repo/
gpgcheck=0
EOF

yum clean expire-cache
yum update -y


touch /etc/puppet/hiera.yaml


systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  /etc/puppet/modules/nailgun/examples/rsyslog-only.pp || [[ $? == 2 ]]


mkdir -p /etc/systemd/system/rsyslog.service.d/
cat << EOF > /etc/systemd/system/rsyslog.service.d/restart.conf
[Service]
Restart=on-failure
RestartSec=5
EOF

systemctl enable rsyslog.service


cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0

[mos]
name=MOS Local Repo
baseurl=file:/var/www/nailgun/mos-centos/x86_64
gpgcheck=0
EOF

yum clean all


#systemctl mask start-container.service
