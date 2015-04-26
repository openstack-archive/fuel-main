#!/bin/bash

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

#
# This script performs initial check and configuration IP forwarding on the
# host system.
#

source ./config.sh

# Check if root login via sudo su works, and save the password. Needed to
# setup accordingly some network configurations, like firewall and NAT
get_sudo_password() {
  echo -e "To configure NAT and Firewall, the script requires the sudo password"
  read -s -p "Enter your sudo password and wait (it won't be prompted): " PASSWORD
  result=$(expect <<ENDOFEXPECT
    spawn sudo su -
    expect "*assword*"
    send -- "$PASSWORD\r"
    expect "*\#*"
    send -- "whoami\r"
    expect "*\#*"
ENDOFEXPECT
  )
  for line in $result; do
    if [[ $line == *root* ]]; then
      echo "OK"
      SUDO_PASSWORD=$PASSWORD
      sudo -k
      return
    fi
  done
  echo "Your sudo password is not correct. Please retry"
  exit 1
}

# Requires sudo privileges for both Linux and Darwin
setup_host_masquerading_settings() {
  current_dir=`pwd`
  result=$(expect <<ENDOFEXPECT
  spawn sudo su -
  expect "*assword*"
  send -- "$SUDO_PASSWORD\r"
  expect "*\#*"
  send -- "pwd\r"
  expect "*\#*"
  send -- "$current_dir/actions/add-firewall-rules.sh $fuel_master_ips\r"
  expect "*\#*"
ENDOFEXPECT
        )
        echo "OK"
}

if [[ "$(uname)" == "Linux" || "$(uname)" == "Darwin" ]]; then
  get_sudo_password
  setup_host_masquerading_settings
elif [ "$(uname -s | cut -c1-6)" != "CYGWIN" ]; then
  echo "$(uname) is not supported operating system."
  exit 1
fi
