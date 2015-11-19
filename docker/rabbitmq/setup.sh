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


mkdir -p /var/lib/hiera /var/log/rabbitmq
touch /var/lib/hiera/common.yaml


systemctl daemon-reload
puppet apply --debug --verbose --color false --detailed-exitcodes \
  /etc/puppet/modules/nailgun/examples/rabbitmq-only.pp || [[ $? == 2 ]]


cat << EOF > /etc/systemd/system/rabbitmq-server.service
[Unit]
Description=RabbitMQ broker
After=syslog.target network.target

[Service]
NotifyAccess=all
User=rabbitmq
Group=rabbitmq
WorkingDirectory=/var/lib/rabbitmq
ExecStartPre=chown -R rabbitmq:rabbitmq /var/lib/rabbitmq
ExecStart=/usr/sbin/rabbitmq-server
ExecStop=/usr/lib/rabbitmq/bin/rabbitmqctl stop

Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl reenable rabbitmq-server.service


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


rm -Rf /var/lib/rabbitmq/mnesia/*
