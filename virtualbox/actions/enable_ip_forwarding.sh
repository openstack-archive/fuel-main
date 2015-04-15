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
  echo "Setting masquerading configuration"
  case "$(uname)" in
    Linux)
      if [ ! -x /sbin/iptables ] ; then
        echo -n "iptables is not available in the system path"
        exit 1
      else
        result=$(expect <<ENDOFEXPECT
          spawn sudo su -
          expect "*assword*"
          send -- "$SUDO_PASSWORD\r"
          expect "*\#*"
          send -- "sysctl -wq net.ipv4.conf.all.forwarding=1\r"
          expect "*\#*"
          send -- "iptables -t nat -A POSTROUTING \
            -o $(ip r | grep default | cut -f5 -d ' ') \
            -s 172.16.1.0/24 \
            ! -d 172.16.1.0/24 \
            -j MASQUERADE\r"
          expect "*\#*"
ENDOFEXPECT
        )
        echo "OK"
      fi
    ;;
    Darwin)
      # Default routed interface
      IF=$(route get default | grep interface | cut -d: -f2 | tr -d ' ')
      # Take the configuration of which interfaces to NAT
      VBOXNET=""
      for interface in 0 $(seq "${#nat_vboxnet[@]}")
      do
        if [[ ${nat_vboxnet[$interface]} = true ]];
        then
          VBOXNET=$VBOXNET"\npass in on vboxnet"$interface
        fi
      done
      # Write pf.conf
      CONF=$(cat <<EOS
#FUEL
\nscrub-anchor "com.apple/*"
\nnat-anchor "com.apple/*"
\nrdr-anchor "com.apple/*"
\ndummynet-anchor "com.apple/*"
\nnat on $IF inet from ! ($IF) to any -> ($IF)
\nanchor "com.apple/*"
\nload anchor "com.apple" from "/etc/pf.anchors/com.apple"
$VBOXNET
\n#/FUEL
EOS
      )
      # Backup the system file and setup nat and PF
      echo -e $CONF > .pftmp
      result=$(expect <<ENDOFEXPECT
        spawn sudo su
        expect "*assword*"
        send -- "$SUDO_PASSWORD\r"
        expect "*\#*"
        send -- "sysctl -wq net.inet.ip.forwarding=1\r"
        expect "*\#*"
        send -- "sysctl -wq net.inet.ip.fw.enable=1\r"
        expect "*\#*"
        send -- "cp -f /etc/pf.conf /etc/pf.conf.bak\r"
        expect "*\#*"
        send -- "cat .pftmp > /etc/pf.conf\r"
        expect "*\#*"
        send -- "pfctl -ef /etc/pf.conf\r"
        expect "*\#*"
ENDOFEXPECT
        )
      rm -f .pftmp
      sudo -k
      echo "OK"
    ;;
    CYGWIN*)
      # TODO
    ;;
    *)
      echo "$(uname) is not a supported operating system."
      exit 1
    ;;
  esac
  rm -f .sudo_pwd
}

# Clean the masquerading settings
clean_host_masquerading_settings() {
  echo "Cleaning masquerading configuration"
  case "$(uname)" in
    Linux)
    ;;
    Darwin)
      # Restores the system's PF
      if [ -z /etc/pf.conf.bak ]; then
        result=$(expect <<ENDOFEXPECT
          spawn sudo su -
          expect "*assword*"
          send -- "$SUDO_PASSWORD\r"
          expect "*\#*"
          send -- "cp -f /etc/pf.conf.bak /etc/pf.conf\r"
          expect "*\#*"
          send -- "pfctl -ef /etc/pf.conf\r"
          expect "*\#*"
ENDOFEXPECT
          )
      fi
    ;;
    CYGWIN*)
        # TODO
    ;;
  esac
  echo "OK"
}

case $(uname) in
  Linux)
    get_sudo_password
  ;;
  Darwin)
    get_sudo_password
    clean_host_masquerading_settings
  ;;
  CYGWIN*)
    # TODO
  ;;
  *)
    echo "$(uname) is not supported operating system."
    exit 1
  ;;
esac

# Clean up the eventual Fuel NAT on host system
setup_host_masquerading_settings
