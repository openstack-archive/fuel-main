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

# Check that HTTPS transport is available to APT
if [ ! -e /usr/lib/apt/methods/https ]; then
    sudo apt-get update
    sudo apt-get install -y apt-transport-https
fi

# Install software
sudo apt-get update
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

echo "Dependency check completed, please proceed with 'make iso' command"
