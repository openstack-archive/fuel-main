#!/bin/bash

cp -r /fuel-main /home/vagrant/
cd /home/vagrant/fuel-main
./prepare-build-env.sh

#workaroud due to https://bugs.launchpad.net/fuel/+bug/1593276
make iso \
  MIRROR_MOS_UBUNTU_ROOT=/mos-repos/ubuntu/master \
  MIRROR_MOS_UBUNTU_SUITE=mos-master \
  MIRROR_FUEL=http://mirror.fuel-infra.org/mos-repos/centos/mos-master-centos7/os/x86_64/

cp fuel*.iso /vagrant"
