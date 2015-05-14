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

# This file contains the functions to manage VMs in through VirtualBox CLI

get_vm_base_path() {
    echo `VBoxManage list systemproperties | grep '^Default machine folder' | sed 's/^Default machine folder\:[ \t]*//'`
}

get_vms_running() {
    echo `VBoxManage list runningvms | sed 's/[ \t]*{.*}//' | sed 's/^"//' | sed 's/"$//'`
}

get_vms_present() {
    echo `VBoxManage list vms | sed 's/[ \t]*{.*}//' | sed 's/^"//' | sed 's/"$//'`
}

is_vm_running() {
    name=$1
    list=$(get_vms_running)

    # Check that the list of running VMs contains the given VM
    for name_in_list in $list; do
        if [[ "$name_in_list" == "$name" ]]; then
            return 0
        fi
    done
    return 1
}

is_vm_present() {
    name=$1
    list=$(get_vms_present)

    for name_in_list in $list; do
        if [[ "$name_in_list" == "$name" ]]; then
            return 0
        fi
    done
    return 1
}

check_running_vms() {
  OIFS=$IFS
  IFS=","
  local hostonly_interfaces=$1
  local list_running_vms=$(VBoxManage list runningvms | sed 's/\" {/\",{/g')
  for vm_name in $list_running_vms; do
    vm_name=$(echo $vm_name | grep "\"" | sed 's/"//g')
    vm_names+="$vm_name,"
  done
  for i in $vm_names; do
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

create_vm() {
    name=$1
    nic=$2
    cpu_cores=$3
    memory_mb=$4
    disk_mb=$5
    os='RedHat_64'

    # There is a chance that some files are left from previous VM instance
    vm_base_path=$(get_vm_base_path)
    vm_path="$vm_base_path/$name/"
    rm -rf "$vm_path"

    # Create virtual machine with the right name and type (assuming CentOS)
    VBoxManage createvm --name $name --ostype $os --register

    # Set the real-time clock (RTC) operate in UTC time
    # Set memory and CPU parameters
    # Set video memory to 16MB, so VirtualBox does not complain about "non-optimal" settings in the UI
    VBoxManage modifyvm $name --rtcuseutc on --memory $memory_mb --cpus $cpu_cores --vram 16

    # Configure main network interface for management/PXE network
    add_hostonly_adapter_to_vm $name 1 "$nic"
    VBoxManage modifyvm $name --boot1 disk --boot2 dvd --boot3 net --boot4 none

    # Configure storage controllers
    VBoxManage storagectl $name --name 'IDE' --add ide --hostiocache on
    VBoxManage storagectl $name --name 'SATA' --add sata --hostiocache on

    # Create and attach the main hard drive
    add_disk_to_vm $name 0 $disk_mb
}

add_hostonly_adapter_to_vm() {
    name=$1
    id=$2
    nic=$3
    echo "Adding hostonly adapter to $name and bridging with host NIC $nic..."

    # Add Intel PRO/1000 MT Desktop (82540EM) card to VM. The card is 1Gbps.
    VBoxManage modifyvm $name --nic${id} hostonly --hostonlyadapter${id} "$nic" --nictype${id} 82540EM \
                        --cableconnected${id} on --macaddress${id} auto
    VBoxManage modifyvm  $name  --nicpromisc${id} allow-all
}

add_nat_adapter_to_vm() {
    name=$1
    id=$2
    nat_network=$3
    echo "Adding NAT adapter to $name for outbound network access through the host system..."

    # Add Intel PRO/1000 MT Desktop (82540EM) card to VM. The card is 1Gbps.
    VBoxManage modifyvm $name --nic${id} nat --nictype${id} 82540EM \
                        --cableconnected${id} on --macaddress${id} auto --natnet${id} "${nat_network}"
    VBoxManage modifyvm  $name  --nicpromisc${id} allow-all
    VBoxManage controlvm $name setlinkstate${id} on
}

add_disk_to_vm() {
    vm_name=$1
    port=$2
    disk_mb=$3

    echo "Adding disk to $vm_name, with size $disk_mb Mb..."

    vm_disk_path="$(get_vm_base_path)/$vm_name/"
    disk_name="${vm_name}_${port}"
    disk_filename="${disk_name}.vdi"
    VBoxManage createhd --filename "$vm_disk_path/$disk_filename" --size $disk_mb --format VDI
    VBoxManage storageattach $vm_name --storagectl 'SATA' --port $port --device 0 --type hdd --medium "$vm_disk_path/$disk_filename"

    # Add serial numbers of disks to slave nodes
    echo "Adding serial numbers of disks to $vm_name..."
    VBoxManage setextradata $vm_name "VBoxInternal/Devices/ahci/0/Config/Port$port/SerialNumber" "VBOX-MIRANTIS-VHD$port"

}

delete_vm() {
    name=$1
    vm_base_path=$(get_vm_base_path)
    vm_path="$vm_base_path/$name/"

    # Power off VM, if it's running
    count=0
    while is_vm_running $name; do
        echo "Stopping Virtual Machine $name..."
        VBoxManage controlvm $name poweroff
        if [[ "$count" != 5 ]]; then
            count=$((count+1))
            sleep 5
        else
            echo "VirtualBox cannot stop VM $name... Exiting"
            exit 1
        fi
    done

    echo "Deleting existing virtual machine $name..."
    while is_vm_present $name
    do
        VBoxManage unregistervm $name --delete
    done
    # Virtualbox does not fully delete VM file structure, so we need to delete the corresponding directory with files as well
    rm -rf "$vm_path"
}

delete_vms_multiple() {
    name_prefix=$1
    list=$(get_vms_present)

    # Loop over the list of VMs and delete them, if its name matches the given refix
    for name in $list; do
        if [[ $name == $name_prefix* ]]; then
            echo "Found existing VM: $name. Deleting it..."
            delete_vm $name
        fi
    done
}

start_vm() {
    name=$1

    # Just start it
    if [[ $headless == 1 ]]; then
        VBoxManage startvm $name --type headless
    else
        VBoxManage startvm $name
    fi
}

mount_iso_to_vm() {
    name=$1
    iso_path=$2

    # Mount ISO to the VM
    VBoxManage storageattach $name --storagectl "IDE" --port 0 --device 0 --type dvddrive --medium "$iso_path"
}

enable_network_boot_for_vm() {
    name=$1

    # Set the right boot priority
    VBoxManage modifyvm $name --boot1 net --boot2 disk --boot3 none --boot4 none --nicbootprio1 1
}

