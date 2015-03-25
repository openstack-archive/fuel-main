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

get_fuel_ifaces() {
  local fuel_iface
  fuel_ifaces=""
  for ip in $fuel_master_ips; do
    fuel_iface=`VBoxManage list hostonlyifs | grep -B5 $ip | grep '^Name' | sed 's/^Name\:[ \t]*//' | uniq | tr "\\n" ","`
    fuel_ifaces+="$fuel_iface"
  done  
  echo $fuel_ifaces
}

get_fuel_name_ifaces() {
  fuel_ifaces=$(get_fuel_ifaces)
  IFS=","
  set -- $fuel_ifaces
  j=0
  for i in $fuel_ifaces; do
    host_nic_name[$j]=$i
    j=$((j+1));
  done
  unset IFS
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
  local found_name=(`VBoxManage list hostonlyifs | egrep -A9 "Name:            $name\$" | awk '/Name/ { $1 = ""; print substr($0, 2) }'`)
  # Change default divider back
  case "$(uname)" in
    CYGWIN*)
      IFS=$OIFS
      ;;
    *)
      ;;
  esac
  # Check that the found interface contains the given interface
  if [[ "$found_name" == "$name" ]]; then
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

create_hostonly_interfaces() {
  # Creating host-only interface
  for (( i = 1; i < 4; i++ )); do
    echo "Creating host-only interface"
    id=`VBoxManage hostonlyif create | sed "s/'/_/g" | cut -d "_" -f2 | sed "s/^_//" | sed "s/_$//"`
    # If it does not exist after creation, let's abort
    if ! is_hostonly_interface_present "$id"; then
      echo "Fatal error. Interface $id does not exist after creation. Exiting"
      exit 1
    else
      echo "Interface" $id "was successfully created"
    fi
    # Disable DHCP
    echo "Disabling DHCP server on interface: $name..."
    # These magic 1 second sleeps around DHCP config are required under Windows/Cygwin
    # due to VBoxSvc COM server accepts next request before previous one is actually finished.
    sleep 1s
    VBoxManage dhcpserver remove --ifname "$name" 2>/dev/null
    sleep 1s
    # Set up IP address and network mask
    ip=(`echo -e $fuel_master_ips | cut -d ' ' -f$i`)
    echo "Configuring IP address $ip and network mask $mask on interface: $name..."
    set -x
    VBoxManage hostonlyif ipconfig "$id" --ip $ip --netmask $mask
    set +x
    # Check what we have created actually.
    # Sometimes VBox occasionally fails to apply settings to the last IFace under Windows
    if !(check_if_iface_settings_applied "$id" $ip $mask); then
      echo "Looks like VirtualBox failed to apply settings for interface $name"
      echo "Sometimes such error happens under Windows."
      echo "Please run launch.sh one more time."
      echo "If this error remains after several attempts, then something really went wrong."
      echo "Aborting."
      exit 1
    fi
  done
}

# Checking that the interface has been removed
check_removed_iface() {
  iface=$1
  if is_hostonly_interface_present "$iface"; then
    echo "Host-only interface \"$iface\" was not removed. Aborting..."
    exit 1
  fi
}

check_running_vms() {
  OIFS=$IFS
  IFS=","
  hostonly_interfaces=$1
  list_running_vms=`VBoxManage list runningvms | awk '{print $1}' | sed 's/"//g' | uniq | tr "\\n" ","`  
  for i in $list_running_vms; do
    for j in $hostonly_interfaces; do
      running_vm=`VBoxManage showvminfo $i | grep "$j"`
      if [[ $? -eq 0 ]]; then
        echo "The \"$i\" VM uses host-only interface \"$j\" and it cannot be removed...."
        echo "You should turn off the \"$i\" virtual machine, run the script again and then the host-only interface will be deleted. Aborting..."
        exit 1
      fi
    done
  done
  IFS=$OIFS
}

delete_fuel_ifaces() {
  fuel_ifaces=$(get_fuel_ifaces)  
  check_running_vms "$fuel_ifaces"
  OIFS=$IFS
  IFS=","
  for interface in $fuel_ifaces; do
    echo "Deleting host-only interface: $interface..."
    VBoxManage hostonlyif remove "$interface"
    check_removed_iface "$interface"
  done
  IFS=$OIFS
}

delete_all_hostonly_interfaces() {
  all_hostonly_interfaces=`VBoxManage list hostonlyifs | grep '^Name' | sed 's/^Name\:[ \t]*//' | uniq | tr "\\n" ","`  
  # Checking that the running virtual machines do not use removable host-only interfaces
  check_running_vms "$all_hostonly_interfaces"
  OIFS=$IFS;IFS=",";list=(`VBoxManage list hostonlyifs | grep '^Name' | sed 's/^Name\:[ \t]*//' | uniq | tr "\\n" ","`);IFS=$OIFS
  # Delete every single hostonly interface in the system
  for interface in "${list[@]}"; do
    echo "Deleting host-only interface: $interface..."
    VBoxManage hostonlyif remove "$interface"
    check_removed_iface "$interface"
  done
}
