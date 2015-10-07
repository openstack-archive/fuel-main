#!/bin/bash -xe

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

#FIXME(mattymo): Update CentOS to 6.6
#yum downgrade -y libcom_err libselinux libselinux-utils

# Install necessary packages
yum install -y sudo ami-creator python-daemon httpd
sed -i '/requiretty/s/^/#/g' /etc/sudoers

# Create loop devices if needed for ami-creator to setup image
for loopdev in $(seq 1 9); do
  mknod "/dev/loop${loopdev}" -m0660 b 7 ${loopdev} || :
done

# Start webserver and wait for it to be up
ln -s /repo/os /var/www/html/os
/usr/sbin/httpd &
#systemctl enable httpd.service
#systemctl start httpd.service

#chmod o+x /lib64/dbus-1/dbus-daemon-launch-helper
/usr/lib/systemd/systemd-localed &

cd /export
exec ami-creator -c /root/fuel-centos.ks -n fuel-centos
