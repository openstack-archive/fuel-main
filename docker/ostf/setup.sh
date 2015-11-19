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

yum install -y --quiet \
  python-fuelclient \
  supervisor \
  postgresql-libs \
  python-editor \
  python-unicodecsv


#FIXME(dteselkin): install the packages below explicitely to
#                  fix their dependenceis BEFORE puppet run
yum install -y --quiet \
  python-saharaclient \
  python-muranoclient \
  python-cliff
sed -i 's/^\(argparse.*\)/#\1/' /usr/lib/python2.7/site-packages/*egg-info/requires.txt


systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  /etc/puppet/modules/nailgun/examples/ostf-only.pp || [[ $? == 2 ]]


cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all


systemctl enable start-container.service
