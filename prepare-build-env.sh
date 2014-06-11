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

# We need to not try to install rubygems on trusty, because it doesn't exists
DISTRO=$(lsb_release -c -s)
if [ $DISTRO == 'trusty' ]; then
    GEMPKG="ruby ruby-dev"
else
    GEMPKG="ruby ruby-dev rubygems"
fi

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
sudo apt-get -y install lxc-docker
fi

# Install software
sudo apt-get update
sudo apt-get -y remove nodejs nodejs-legacy npm
sudo apt-get -y install software-properties-common python-software-properties
sudo add-apt-repository -y ppa:chris-lea/node.js
sudo apt-get update
sudo apt-get -y install build-essential make git $GEMPKG debootstrap createrepo \
	python-setuptools yum yum-utils libmysqlclient-dev isomd5sum \
	python-nose libvirt-bin python-ipaddr python-paramiko python-yaml \
	python-pip kpartx extlinux unzip genisoimage nodejs multistrap \
	lrzip python-daemon
sudo gem install bundler -v 1.2.1
sudo gem install builder
sudo pip install xmlbuilder jinja2
sudo npm install -g grunt-cli

# Add account to sudoers
if sudo grep "`whoami` ALL=(ALL) NOPASSWD: ALL" /etc/sudoers; then
	echo "Required /etc/sudoers record found"
else
	echo "Required /etc/sudoers record not found, adding it..."
	echo "`whoami` ALL=(ALL) NOPASSWD: ALL" | sudo tee -a /etc/sudoers
fi

# Fix tmp folder ownership
mkdir -p ~/tmp
sudo chown $USER:$USER ~/tmp

echo "Dependency check complete, please proceed with 'make iso' command"
