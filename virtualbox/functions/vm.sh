#!/bin/bash

# This file contains the functions to manage VMs in through VirtualBox CLI

get_vm_base_path() {
    echo -e `VBoxManage list systemproperties | grep '^Default machine folder' | sed 's/^Default machine folder\:[ \t]*//'` 
}

get_vms_running() {
    echo -e `VBoxManage list runningvms | sed 's/[ \t]*{.*}//' | sed 's/^"//' | sed 's/"$//'`
}

get_vms_present() {
    echo -e `VBoxManage list vms | sed 's/[ \t]*{.*}//' | sed 's/^"//' | sed 's/"$//'`
}

is_vm_running() {
    name=$1
    list=$(get_vms_running)

    # Check that the list of running VMs contains the given VM
    if [[ $list = *$name* ]]; then
        return 0
    else
        return 1
    fi
}

create_vm() {
    name=$1
    nic=$2
    cpu_cores=$3
    memory_mb=$4
    disk_mb=$5
   
    # Create virtual machine with the right name and type (assuming CentOS) 
    VBoxManage createvm --name $name --ostype RedHat_64 --register

    # Set the real-time clock (RTC) operate in UTC time
    # Set memory and CPU parameters
    # Set video memory to 16MB, so VirtualBox does not complain about "non-optimal" settings in the UI
    VBoxManage modifyvm $name --rtcuseutc on --memory $memory_mb --cpus $cpu_cores --vram 16

    # Configure main network interface for management/PXE network
    add_hostonly_adapter_to_vm $name 1 $nic

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
    VBoxManage modifyvm $name --nic${id} hostonly --hostonlyadapter${id} $nic --nictype${id} 82540EM \
                        --cableconnected${id} on --macaddress${id} auto
    VBoxManage controlvm $name setlinkstate${id} on
}

add_nat_adapter_to_vm() {
    name=$1
    id=$2
    nat_network=$3
    echo "Adding NAT adapter to $name for outbound network access through the host system..."

    # Add Intel PRO/1000 MT Desktop (82540EM) card to VM. The card is 1Gbps.
    VBoxManage modifyvm $name --nic${id} nat --nictype${id} 82540EM \
                        --cableconnected${id} on --macaddress${id} auto --natnet${id} "${nat_network}"
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
    VBoxManage createhd --filename "$vm_disk_path/$disk_name" --size $disk_mb --format VDI
    VBoxManage storageattach $vm_name --storagectl 'SATA' --port $port --device 0 --type hdd --medium "$vm_disk_path/$disk_filename"
}

delete_vm() {
    name=$1
    vm_base_path=$(get_vm_base_path)
    vm_path="$vm_base_path/$name/"

    # Power off VM, if it's running
    if is_vm_running $name; then
        VBoxManage controlvm $name poweroff
    fi

    # Virtualbox does not fully delete VM file structure, so we need to delete the corresponding directory with files as well 
    if [ -d "$vm_path"  ]; then
        echo "Deleting existing virtual machine $name..."
        VBoxManage unregistervm $name --delete
        rm -rf "$vm_path"
    fi
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
    #VBoxManage startvm $name --type headless
    VBoxManage startvm $name
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
    VBoxManage modifyvm $name --boot1 disk --boot2 net --boot3 none --boot4 none --nicbootprio1 1
}

