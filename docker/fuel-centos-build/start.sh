#!/bin/bash -xe

# Clean rpm locks before puppet run.
# See ticket https://bugs.launchpad.net/fuel/+bug/1339236
rm -f /var/lib/rpm/__db.*
rpm --rebuilddb

#Create loop devices if needed for ami-creator to setup image
for loopdev in `seq 1 9`; do
  mknod "/dev/loop${loopdev}" -m0660 b 7 ${loopdev} || :
done
cd /export
ami-creator -c /root/fuel-centos.ks -n fuel-centos

