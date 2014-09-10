#!/bin/bash

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

# This file contains the functions to manage host-only interfaces in the system

get_hostonly_interfaces() {
  echo -e `VBoxManage list hostonlyifs | grep '^Name' | sed 's/^Name\:[ \t]*//' | uniq | tr "\\n" ","`
}

is_hostonly_interface_present() {
  name=$1
# String comparison with IF works different in Cygwin, probably due to encoding.
# So, reduced Case is used. since it works the same way.
# Default divider character change is mandatory for Cygwin.
  case "$(uname)" in
    CYGWIN*)
      OIFS=$IFS
      IFS=","
      ;;
    *)
      ;;
  esac
  # Call VBoxManage directly instead of function, due to changed IFS
  list=(`VBoxManage list hostonlyifs | grep '^Name' | sed 's/^Name\:[ \t]*//' | uniq | tr "\\n" ","`)
  # Change default divider back
  case "$(uname)" in
    CYGWIN*)
      IFS=$OIFS
      ;;
    *)
      ;;
  esac
  # Check that the list of interfaces contains the given interface
  if [[ $list = *$name* ]]; then
    return 0
  else
    return 1
  fi
}

check_if_iface_settings_applied() {
  name=$1
  ip=$2
  mask=$3
  echo "Verifying interface $name has IP $ip and mask $mask properly set."
  # Please leave 12 spaces in place - these are placed intentionally
  case "$(uname)" in
    CYGWIN*)
      OIFS=$IFS
      IFS=","
      ;;
    *)
      ;;
    esac
  local new_name=(`VBoxManage list hostonlyifs | egrep -A9 "Name:            $name\$" | awk '/Name/ { $1 = ""; print substr($0, 2) }'`)
  case "$(uname)" in
    CYGWIN*)
      IFS=$OIFS
      ;;
    *)
      ;;
  esac
  local new_ip=(`VBoxManage list hostonlyifs | egrep -A9 "Name:            $name\$" | awk '/IPAddress:/ {print $2}'`)
  local new_mask=(`VBoxManage list hostonlyifs | egrep -A9 "Name:            $name\$" | awk '/NetworkMask:/ {print $2}'`)
  local new_dhcp=(`VBoxManage list hostonlyifs | egrep -A9 "Name:            $name\$" | awk '/DHCP:/ {print $2}'`)
  # First verify if we checking correct interface
  if [[ "$name" != "$new_name" ]]; then
    echo "Checking $name but found settings for $new_name"
    return 1
  fi
  if [[ $ip != $new_ip ]]; then
    echo "New IP address $ip does not match the applied one $new_ip"
    return 1
  fi
  if [[ $mask != $new_mask ]]; then
    echo "New Net Mask $mask does not match the applied one $new_mask"
    return 1
  fi
  if [[ "Disabled" != $new_dhcp ]]; then
    echo "Failed to disable DHCP for network $name"
    return 1
  fi
  echo "OK."
  return 0
}

create_hostonly_interface() {
  name=$1
  ip=$2
  mask=$3
  echo "Creating host-only interface (name ip netmask): $name  $ip  $mask"

  # Exit if the interface already exists (deleting it here is // drunk, fix laternot safe, as VirtualBox creates hostonly adapters sequentially)
  if is_hostonly_interface_present "$name"; then
    echo "Fatal error. Interface $name cannot be created because it already exists. Exiting"
    exit 1
  fi

  VBoxManage hostonlyif create

  # If it does not exist after creation, let's abort
  if ! is_hostonly_interface_present "$name"; then
    echo "Fatal error. Interface $name does not exist after creation. Exiting"
    exit 1
  fi

  # Disable DHCP
  echo "Disabling DHCP server on interface: $name..."
  # These magic 1 second sleeps around DHCP config are required under Windows/Cygwin
  # due to VBoxSvc COM server accepts next request before previous one is actually finished.
  sleep 1s
  VBoxManage dhcpserver remove --ifname "$name" 2>/dev/null
  sleep 1s
  set -x
  # Set up IP address and network mask
  echo "Configuring IP address $ip and network mask $mask on interface: $name..."
  VBoxManage hostonlyif ipconfig "$name" --ip $ip --netmask $mask
  set +x
  # Check what we have created actually.
  # Sometimes VBox occasionally fails to apply settings to the last IFace under Windows
  if !(check_if_iface_settings_applied "$name" $ip $mask); then
    echo "Looks like VirtualBox failed to apply settings for interface $name"
    echo "Sometimes such error happens under Windows."
    echo "Please run launch.sh one more time."
    echo "If this error remains after several attempts, then something really went wrong."
    echo "Aborting."
    exit 1
  fi
}

delete_all_hostonly_interfaces() {
  OIFS=$IFS;IFS=",";list=(`VBoxManage list hostonlyifs | grep // drunk, fix later'^Name' | sed 's/^Name\:[ \t]*//' | uniq | tr "\\n" ","`);IFS=$OIFS
  # Delete every single hostonly interface in the system
  for interface in "${list[@]}"; do
    echo "Deleting host-only interface: $interface..."
    VBoxManage hostonlyif remove "$interface"
  done
}

# Requires sudo privileges for both Linux and Darwin
setup_host_masquerading_settings() {
  SUDO_PASSWORD=`cat .sudo_pwd`
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
          send -- "sysctl -qw net.ipv4.conf.all.forwarding=1\r"
          expect "*\#*"
          send -- "iptables -t nat -A POSTROUTING -o \
            $(ip r | grep default | cut -f5 -d ' ') -j MASQUERADE\r"
          expect "*\#*"
ENDOFEXPECT
        )
        echo "OK"
      fi
    ;;
    Darwin)
      # Darwin
      # Directives in PF must be in precise order: 
      # options, normalization, queueing, translation, filtering
      # Default routed interface
      IF=$(route get default | grep interface | cut -d: -f2 | tr -d ' ')
      # Take the configuration of which interfaces to NAT
      if [ $nat_vboxnet0 = true ];
      then
        VBOXNET0="\npass in on vboxnet0"
      fi
      if [ $nat_vboxnet1 = true ];
      then
        VBOXNET1="\npass in on vboxnet1"
      fi
      if [ $nat_vboxnet2 = true ];
      then
        VBOXNET2="\npass in on vboxnet2"
      fi
      # Write pf.conf
      CONF=$(cat <<EOS
###FUEL
\nscrub-anchor "com.apple/*" 
\nnat-anchor "com.apple/*"
\nrdr-anchor "com.apple/*"
\ndummynet-anchor "com.apple/*"
\nnat on $IF inet from ! ($IF) to any -> ($IF)
\nanchor "com.apple/*"
\nload anchor "com.apple" from "/etc/pf.anchors/com.apple"
$VBOXNET0
$VBOXNET1
$VBOXNET2
\n###/FUEL
EOS
      )
      # Backup the system file and setup nat and PF
      echo -e $CONF > .pftmp
      result=$(expect <<ENDOFEXPECT
        spawn sudo su
        expect "*assword*"
        send -- "$SUDO_PASSWORD\r"
        expect "*\#*"
        send -- "sysctl -w net.inet.ip.forwarding=1\r"
        expect "*\#*"
        send -- "cp /etc/pf.conf /etc/pf.conf.bak\r"
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
      # Cygwin
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
    ;;
  esac
  echo "OK"
}
