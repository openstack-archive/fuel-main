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
    echo -e `VBoxManage list hostonlyifs | grep '^Name' | sed 's/^Name\:[ \t]*//' | uniq` 
}

is_hostonly_interface_present() {
    name=$1
    list=$(get_hostonly_interfaces)
    
    # Check that the list of interfaces contains the given interface
    if [[ $list = *$name* ]]; then
        return 0
    else
        return 1
    fi
}

create_hostonly_interface() {
    name=$1
    ip=$2
    mask=$3
    echo "Creating host-only interface (name ip netmask): $name  $ip  $mask"

    # Exit if the interface already exists (deleting it here is not safe, as VirtualBox creates hostonly adapters sequentially)
    if is_hostonly_interface_present $name; then
        echo "Fatal error. Interface $name cannot be created because it already exists. Exiting"
        exit 1
    fi

    VBoxManage hostonlyif create

    # If it does not exist after creation, let's abort
    if ! is_hostonly_interface_present $name; then
        echo "Fatal error. Interface $name does not exist after creation. Exiting"
        exit 1
    fi

    # Disable DHCP
    echo "Disabling DHCP server on interface: $name..."
    VBoxManage dhcpserver remove --ifname $name 2>/dev/null

    # Set up IP address and network mask
    echo "Configuring IP address $ip and network mask $mask on interface: $name..."
    VBoxManage hostonlyif ipconfig $name --ip $ip --netmask $mask
}

delete_all_hostonly_interfaces() {
    list=$(get_hostonly_interfaces)

    # Delete every single hostonly interface in the system
    for interface in $list; do
        echo "Deleting host-only interface: $interface..."
        VBoxManage hostonlyif remove $interface
    done
}

