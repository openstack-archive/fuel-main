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

# - We need not try to install rubygems on trusty, because it doesn't exists

# install yum and yum-utils from trusty, so it can handle the meta-data
# of OSCI rpm repositories. Works around ISO build failure (LP #1381535).
update_yum_utils ()
{
    local pkgs="yum_3.4.3-2ubuntu1_all.deb yum-utils_1.1.31-2_all.deb"
    # required for new yum-utils
    local deps="python-iniparse"
    local mirror="https://launchpad.net/ubuntu/+archive/primary/+files"
    sudo apt-get install $deps
    for pkg in $pkgs; do
	    rm -f $pkg >/dev/null 2>&1
	    wget "${mirror}/${pkg}"
	    sudo dpkg -i $pkg
    done
}

DISTRO=$(lsb_release -c -s)

case "${DISTRO}" in

  trusty)
    GEMPKG="ruby ruby-dev"
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys D5A05778
    echo "deb http://mirror.fuel-infra.org/devops/ubuntu/ ./" | sudo tee /etc/apt/sources.list.d/fuel-devops.list
    sudo apt-get update && sudo apt-get -y install nodejs nodejs-legacy npm
    ;;

  precise)
    GEMPKG="ruby ruby-dev rubygems"
    # be sure, we will use nodejs from chris-lea
    sudo tee /etc/apt/preferences.d/fuel-pin-300 <<EOF
Package: *nodejs*
Pin: release o=LP-PPA-chris-lea-node.js
Pin-Priority: 1000
EOF

    # we need to use add-apt-repository command
    sudo apt-get -y install software-properties-common python-software-properties

    if hash nodejs 2> /dev/null; then
      echo "Nodejs found, checking if it has proper version"
      # Install correct nodejs from chris-lea
      if ! dpkg-query -W -f='${Version}\n' nodejs | grep -q "1chl1"; then
        # we don't have nodejs from chris-lea, need remove previous version
        sudo apt-get -y remove nodejs npm
        # install chris-lea repo, the package itself will be installed later
        sudo add-apt-repository -y ppa:chris-lea/node.js
      fi
    else
      # just add repository, package nodejs will be installed from
      sudo add-apt-repository -y ppa:chris-lea/node.js
    fi
      sudo apt-get update && sudo apt-get -y install nodejs
      ;;

  *)
    echo "We currently doesn't support building on your distribution ${DISTRO}"
    exit 1;
esac

# Check if docker is installed
if hash docker 2>/dev/null; then
  echo "Docker binary found, checking if service is running..."
  ps cax | grep docker > /dev/null
  if [ $? -eq 0 ]; then
    echo "Docker is running."
  else
    echo "Process is not running, starting it..."
    sudo service docker start
  fi
else
  # Install docker repository
  # Check that HTTPS transport is available to APT
  if [ ! -e /usr/lib/apt/methods/https ]; then
    sudo apt-get update
    sudo apt-get -y install -y apt-transport-https
  fi
  # Add the repository to APT sources
  echo deb http://mirror.yandex.ru/mirrors/docker/ docker main | sudo tee /etc/apt/sources.list.d/docker.list
  # Import the repository key
  sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
  # Install docker
  sudo apt-get update
  sudo apt-get -y install lxc-docker-1.5.0
fi

# Install software
sudo apt-get update
sudo apt-get -y install build-essential make git $GEMPKG debootstrap createrepo \
  python-setuptools yum yum-utils libmysqlclient-dev isomd5sum bc \
  python-nose libvirt-bin python-ipaddr python-paramiko python-yaml \
  python-pip kpartx extlinux unzip genisoimage syslinux debmirror \
  lrzip python-daemon python-dev libparse-debcontrol-perl reprepro
sudo gem install bundler -v 1.2.1
sudo gem install builder
sudo pip install xmlbuilder jinja2 pbr
sudo npm install -g gulp
sudo chown -R `whoami`.`id -gn` `npm config get cache`

# Add account to sudoers
if sudo grep "`whoami` ALL=(ALL) NOPASSWD: ALL" /etc/sudoers; then
  echo "Required /etc/sudoers record found"
else
  echo "Required /etc/sudoers record not found, adding it..."
  echo "`whoami` ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers
fi

case "${DISTRO}" in
	precise)
		update_yum_utils
		;;
esac

# Fix tmp folder ownership
[ -d ~/tmp ] && sudo chown -R `whoami`.`id -gn` ~/tmp || mkdir ~/tmp

echo "Dependency check completed, please proceed with 'make iso' command"
