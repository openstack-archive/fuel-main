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


# Install systemd
yum -y install systemd
yum clean all

cd /lib/systemd/system/sysinit.target.wants/
for i in *; do
  [ $i == systemd-tmpfiles-setup.service ] || rm -f $i
done

rm -f /lib/systemd/system/multi-user.target.wants/*
rm -f /etc/systemd/system/*.wants/*
rm -f /lib/systemd/system/local-fs.target.wants/*
rm -f /lib/systemd/system/sockets.target.wants/*udev*
rm -f /lib/systemd/system/sockets.target.wants/*initctl*
rm -f /lib/systemd/system/basic.target.wants/*
rm -f /lib/systemd/system/anaconda.target.wants/*


# Create loop devices if needed for ami-creator to setup image
for loopdev in $(seq 1 9); do
  mknod "/dev/loop${loopdev}" -m0660 b 7 ${loopdev} || :
done


# Start webserver and wait for it to be up
ln -s /repo/os /var/www/html/os
systemctl enable httpd.service

/usr/sbin/init &
sleep 10

cd /export
ami-creator -c /root/fuel-centos.ks -n fuel-centos
