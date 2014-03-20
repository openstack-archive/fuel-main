#!/bin/bash

# Include the script with handy functions to operate VMs and Virtual networking
source config.sh
source functions/vm.sh
source functions/network.sh

#default language
export LC_LANG=C

#Installation additional packages for PXE boot
for i in $package_list
do apt-get install -y $i
done


# Check for ISO image to be available
echo -n "Checking for Fuel Web ISO image... "
if [ -z $iso_path ]; then
    echo "Fuel Web image is not found. Please download it and put under 'iso' directory."
    exit 1
fi
echo "OK"

# Check for expect
echo -n "Checking for 'expect'... "
expect -v >/dev/null 2>&1 || { echo >&2 "'expect' is not available in the path, but it's required. Please install 'expect' package. Aborting."; exit 1; }
echo "OK"

# Check for virsh
echo -n "Checking for 'virsh'... "
virsh -v >/dev/null 2>&1 || { echo >&2 "'virsh' is not available in the path, but it's required. Please install 'libvirt' package. Aborting."; exit 1; }
echo "OK"

#Check for qemu-img
echo -n "Checking for 'qemu-img'... "
which qemu-img >/dev/null && { echo >&2 "OK"; } || { echo  >&2 "'qemu-img' tool is not installed."; exit 1; }

# Delete all VMs from the previous Fuel Web installation
delete_vms_multiple $env_name_prefix

#Delete previous networks
delete_previous_networks

#check_all_bridges
check_all_bridges || exit 1

#create_all_networks
create_all_networks

#create	custom network for pxe boot
create_pxe_network

#setting up NFS service
nfs_setting_up

#settings up TFTP boot
tftpboot
