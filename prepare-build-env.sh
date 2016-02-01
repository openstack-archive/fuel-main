#!/bin/bash -x

#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

#    This script will install all the required packages necessary for
#    building a Fuel ISO.

# Install docker repository
# Check that HTTPS transport is available to APT
if [ ! -e /usr/lib/apt/methods/https ]; then
    sudo apt-get update
    sudo apt-get install -y apt-transport-https
fi
# Add the repository to APT sources
echo deb http://mirror.yandex.ru/mirrors/docker/ docker main | sudo tee /etc/apt/sources.list.d/docker.list
# Import the repository key
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
# Install docker
sudo apt-get update
sudo apt-get -y install lxc-docker-1.6.2
# add user to docker group
sudo usermod -a -G docker "$(whoami)"


# Install software
sudo apt-get update
# we need linux-image-generic-lts-vivid kernel because of bug: https://bugs.launchpad.net/mos/+bug/1484485
sudo apt-get -y install \
  build-essential \
  createrepo \
  debmirror \
  debootstrap \
  devscripts \
  dosfstools \
  extlinux \
  git \
  isomd5sum \
  libparse-debcontrol-perl \
  linux-image-generic-lts-vivid \
  lrzip \
  python-jinja2 \
  python-yaml \
  reprepro \
  rpm \
  syslinux \
  unzip \
  xorriso \
  yum \
  yum-utils

# Add account to sudoers
echo "Updating /etc/sudoers.d/fuel-iso"
cat << EOF | sudo tee /etc/sudoers.d/fuel-iso
Defaults	env_keep += "http_proxy https_proxy no_proxy"
${USER} ALL=(ALL) NOPASSWD:ALL
EOF

echo "Dependency check completed, please reboot system and proceed with 'make iso' command"
