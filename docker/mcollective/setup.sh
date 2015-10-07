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

yum install -y --quiet sudo mcollective shotgun fuel-agent fuel-provisioning-scripts

# /var/lib/fuel/ibp is a mount point for IBP host volume
RUN mkdir -p /var/lib/hiera /var/lib/fuel/ibp
touch /etc/puppet/hiera.yaml /var/lib/hiera/common.yaml

/usr/bin/puppet apply --detailed-exitcodes -d -v /etc/puppet/modules/mcollective/examples/mcollective-server-only.pp || [[ $? == 2 ]]

#FIXME(mattymo): Workaround to make diagnostic snapshots work
mkdir -p /opt/nailgun/bin /var/www/nailgun/dump
ln -s /usr/bin/nailgun_dump /opt/nailgun/bin/nailgun_dump

# let's disable some services and commands since we don't need them in our container
cat << EOF > /etc/init.d/mcollective
#!/bin/bash
#chkconfig: 345 20 80
exit 0
EOF

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all

systemctl enable start-container.service
