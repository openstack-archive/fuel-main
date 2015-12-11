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

packages="sudo mcollective shotgun fuel-agent fuel-provisioning-scripts psmisc daemonize"
echo $packages | xargs -n1 yum install -y

# /var/lib/fuel/ibp is a mount point for IBP host volume
mkdir -p /var/lib/hiera /var/lib/fuel/ibp
touch /etc/puppet/hiera.yaml /var/lib/hiera/common.yaml


systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  /etc/puppet/modules/nailgun/examples/mcollective-only.pp || [[ $? == 2 ]]


#FIXME(mattymo): Workaround to make diagnostic snapshots work
mkdir -p /opt/nailgun/bin /var/www/nailgun/dump
ln -s /usr/bin/nailgun_dump /opt/nailgun/bin/nailgun_dump


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
