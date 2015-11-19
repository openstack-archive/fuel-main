#!/bin/bash -xe

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

cat << EOF > /etc/yum.repos.d/nailgun.repo
[nailgun]
name=Nailgun Local Repo
baseurl=file:///repo/os/x86_64/
gpgcheck=0

[mos]
name=MOS Local Repo
baseurl=file:///mos-repo/
gpgcheck=0
EOF

# Install necessary packages
yum install -y --quiet \
  sudo \
  ami-creator \
  python-daemon \
  httpd

sed -i '/requiretty/s/^/#/g' /etc/sudoers


# Create loop devices if needed for ami-creator to setup image
for loopdev in $(seq 1 9); do
  mknod "/dev/loop${loopdev}" -m0660 b 7 ${loopdev} || :
done


# Start webserver and wait for it to be up
mkdir -p /var/www/html/repo
ln -s /repo/os /var/www/html/repo/os
ln -s /mos-repo /var/www/html/

/usr/sbin/httpd &
/usr/lib/systemd/systemd-localed &

cd /export
ami-creator -c /root/fuel-centos.ks -n fuel-centos
