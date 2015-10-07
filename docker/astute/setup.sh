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

puppet apply --color false --detailed-exitcodes --debug --verbose \
  /etc/puppet/modules/nailgun/examples/astute-only.pp || [[ $? == 2 ]]

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:/var/www/nailgun/centos/x86_64
gpgcheck=0
EOF

yum clean all
