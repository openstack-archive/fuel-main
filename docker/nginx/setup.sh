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

mkdir -p /var/www/nailgun
chmod 755 /var/www/nailgun

systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  /etc/puppet/modules/nailgun/examples/nginx-only.pp || [[ $? == 2 ]]

mkdir -p /etc/systemd/system/nginx.service.d/
cat << EOF > /etc/systemd/system/nginx.service.d/restart.conf
[Service]
Restart=on-failure
RestartSec=5
EOF

systemctl enable nginx.service

# FIXME (dteselkin): Ideally we should make a package for all these systemd
#                    unit files instead of hardcoding them in a setup script
#                    #1519412
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
