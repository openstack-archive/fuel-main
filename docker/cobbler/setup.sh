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

ln -s /etc/dnsmasq.conf /etc/cobbler.dnsmasq.conf

yum install -y --quiet httpd cobbler dnsmasq xinetd tftp-server

mkdir -p /etc/systemd/system/{httpd,cobblerd,tftp,dnsmasq,xinetd}.service.d/
for srv in httpd cobblerd tftp dnsmasq xinetd; do
cat << EOF > /etc/systemd/system/${srv}.service.d/restart.conf
[Service]
Restart=always
RestartSec=5
FailureAction=reboot-force
EOF
done
systemctl set-default multi-user.target

systemctl enable httpd.service \
	cobblerd.service \
	tftp.service \
	dnsmasq.service \
	xinetd.service

#Workaround for dnsmasq startup and create blank SSH key during build
cat << EOF > /etc/sysconfig/network
NETWORKING=yes
HOSTNAME=$HOSTNAME
EOF

mkdir -p /root/.ssh
chmod 700 /root/.ssh
touch /root/.ssh/id_rsa.pub
systemctl restart httpd.service

puppet apply --color false --detailed-exitcodes --debug --verbose \
  /etc/puppet/modules/nailgun/examples/cobbler-only.pp || [[ $? == 2 ]]

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all

systemctl enable start-container.service
