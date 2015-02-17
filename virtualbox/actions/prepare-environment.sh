#!/bin/bash
# set -x

#    Copyright 2013 Mirantis, Inc.
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

#
# This script performs initial check and configuration of the host system. It:
#   - verifies that all available command-line tools are present on the host system
#
# We are avoiding using 'which' because of http://stackoverflow.com/questions/592620/check-if-a-program-exists-from-a-bash-script 
#

# Include the script with handy functions to operate VMs and VirtualBox networking
source ./config.sh 
source ./functions/vm.sh
source ./functions/network.sh

# Check for procps package
if [ "$(uname -s | cut -c1-6)" = "CYGWIN" ]; then
  echo -n "Checking for 'free'... "
  type free >/dev/null 2>&1
  if [ $? -eq 1 ]; then
    echo "\"free\" is not available in the path, but it's required. Please install the \"procps\" package. Aborting."
    exit 1
  else
    echo "OK"
  fi
fi

# Check for expect
echo -n "Checking for 'expect'... "
type expect >/dev/null 2>&1
if [ $? -eq 1 ]; then
  echo "\"expect\" is not available in the path, but it's required. Please install Tcl \"expect\" package. Aborting."
  exit 1
else
  echo "OK"
fi

# Check for VirtualBox
echo "If you run this script under Cygwin, you may have to add path to VirtualBox directory to your PATH. "
echo "Usually it is enough to run \"export PATH=\$PATH:\"/cygdrive/c/Program Files/Oracle/VirtualBox\" "
echo -n "Checking for \"VBoxManage\"... "
type VBoxManage >/dev/null 2>&1
if [ $? -eq 1 ]; then
  echo "\"VBoxManage\" is not available in the path, but it's required. Likely, VirtualBox is not installed. Aborting."
  exit 1
else
  echo "OK"
fi

# Check for VirtualBox Extension Pack
echo -n "Checking for VirtualBox Extension Pack... "
extpacks=`VBoxManage list extpacks | grep 'Usable' | grep 'true' | wc -l`
if [ "$extpacks" -le 0 ]; then
    echo >&2 "VirtualBox Extension Pack is not installed. Please, download and install it from the official VirtualBox web site at https://www.virtualbox.org/wiki/Downloads"; exit 1;
fi
echo "OK"

# Check for ISO image to be available
echo -n "Checking for Mirantis OpenStack ISO image... "
if [ -z $iso_path ]; then
    echo "Mirantis OpenStack image is not found. Please download it from software.mirantis.com and put under the 'iso' directory."
    exit 1
fi
echo "OK"
echo "Going to use Mirantis OpenStack ISO file $iso_path"

# Check if SSH is installed. Cygwin does not install SSH by default.
echo -n "Checking if SSH client installed... "
type ssh >/dev/null 2>&1
if [ $? -eq 1 ]; then
  echo "SSH client is not installed. Please install the \"openssh\" package if you run this script under Cygwin. Aborting."
  exit 1
else
  echo "OK"
fi

echo -n "Checking if ipconfig or ifconfig installed... "
case "$(uname)" in
  Linux | Darwin)
    if [ ! -x /sbin/ifconfig ] ; then
      echo "No ifconfig available at /sbin/ifconfig path! This path is hard-coded into VBoxNetAdpCtl utility." 
      echo "Please install ifconfig or create symlink to proper interface configuration utility. Aborting."
      exit 1
    fi
  ;;
  CYGWIN*)
    # Cygwin does not use ifconfig at all and even has no link to it.
    # It uses built-in Windows ipconfig utility instead.
    type ipconfig >/dev/null 2>&1
    if [ $? -eq 1 ]; then
      echo "No ipconfig available in Cygwin environment. Please check you can run ipconfig from Cygwin command prompt. Aborting."
      exit 1
    fi
  ;;
  *)
    echo "$(uname) is not supported operating system."
    exit 1
  ;;
esac
echo "OK"

# Report success
echo "Setup is done."
