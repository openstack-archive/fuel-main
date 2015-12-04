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

for repo in ${EXTRA_RPM_REPOS}; do
  IFS=, read -a repo_args <<< "$repo"
  cat << EOF >> /etc/yum.repos.d/nailgun.repo

[extra-repo-${repo_args[0]}]
name=MOS Extra Repo ${repo_args[0]}
baseurl=http://$(route -n | awk '/^0.0.0.0/ {print $2}'):${DOCKER_PORT}/extra-repos/${repo_args[0]}
gpgcheck=0
EOF
done

yum clean expire-cache
yum update -y


ln -s /etc/dnsmasq.conf /etc/cobbler.dnsmasq.conf

packages="httpd cobbler dnsmasq xinetd tftp-server"
echo $packages | xargs -n1 yum install -y


mkdir -p /etc/systemd/system/{httpd,cobblerd,tftp,dnsmasq,xinetd}.service.d/
for srv in httpd cobblerd tftp dnsmasq xinetd; do
cat << EOF > /etc/systemd/system/${srv}.service.d/restart.conf
[Service]
Restart=on-failure
RestartSec=5
EOF
done

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


systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  /etc/puppet/modules/nailgun/examples/cobbler-only.pp || [[ $? == 2 ]]


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


systemctl enable start-container.service
