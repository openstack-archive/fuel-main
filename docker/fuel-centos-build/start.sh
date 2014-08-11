#!/bin/bash

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

rpm -i http://mirror.logol.ru/epel/6/i386/epel-release-6-8.noarch.rpm
yum install -y livecd-tools git python-pip
pip install ez_setup
git clone https://github.com/katzj/ami-creator.git
cd ami-creator/ && python setup.py install
#Create loop devices for ami-creator to setup image
for loopdev in `seq 1 9`; do
  mknod "/dev/loop${loopdev}" -m0660 b 7 ${loopdev}
done

cd /export && ami-creator -c /root/fuel-centos.ks -n fuel-centos -v
