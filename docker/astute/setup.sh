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
  psmisc \
  python-editor \
  nailgun-mcagents \
  sysstat \
  rubygem-amqp \
  rubygem-amq-protocol \
  rubygem-i18n \
  rubygem-tzinfo \
  rubygem-minitest \
  rubygem-open4 \
  rubygem-Platform \
  rubygem-symboltable \
  rubygem-thread_safe \
  rubygem-eventmachine \
  fuel-agent


#FIXME(dteselkin): use correct versions of rubygem packages
sed -i '/amq-protocol/ s/~>/>=/' /usr/share/gems/specifications/amqp-*.gemspec


systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  /etc/puppet/modules/nailgun/examples/astute-only.pp || [[ $? == 2 ]]


mkdir -p /etc/systemd/system/supervisord.service.d/
cat << EOF > /etc/systemd/system/supervisord.service.d/restart.conf
[Service]
Restart=always
RestartSec=5
StartLimitAction=reboot-force
EOF

systemctl enable supervisord.service


cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all

systemctl enable start-container.service
