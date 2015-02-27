#!/bin/bash -xe

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

#FIXME(mattymo): Update CentOS to 6.6
yum downgrade -y libcom_err libselinux libselinux-utils

# Install necessary packages
yum install -y sudo ami-creator python-daemon

sed -i '/requiretty/s/^/#/g' /etc/sudoers

# Create loop devices if needed for ami-creator to setup image
for loopdev in `seq 1 9`; do
  mknod "/dev/loop${loopdev}" -m0660 b 7 ${loopdev} || :
done
(cd /repo && python /usr/local/bin/simple_http_daemon.py 80 /var/run/simple_http_daemon.pid) &
cd /export
ami-creator -c /root/fuel-centos.ks -n fuel-centos
