#!/bin/bash 

#
# This script creates a master node for the product, launches its installation,
# and waits for its completion
#

# Include the handy functions to operate VMs and track ISO installation progress
source config.sh
source functions/vm.sh
source functions/product.sh

# Create master node for the product
name="${vm_name_prefix}master"
delete_vm $name
echo
create_vm $name ${host_nic_name[0]} $vm_master_cpu_cores $vm_master_memory_mb $vm_master_disk_mb
echo

# Add additional NICs
add_hostonly_adapter_to_vm $name 2 ${host_nic_name[1]}

# Add NAT adapter for internet access
add_nat_adapter_to_vm $name 3 $vm_master_nat_network

# Mount ISO with installer
mount_iso_to_vm $name $iso_path

# Start virtual machine with the master node
echo
start_vm $name

# Wait until the machine gets installed and Puppet completes its run
wait_for_product_vm_to_install $vm_master_ip $vm_master_username $vm_master_password "$vm_master_prompt"

# Enable outbound network/internet access for the machine
enable_outbound_network_for_product_vm $vm_master_ip $vm_master_username $vm_master_password "$vm_master_prompt" 3 $vm_master_nat_gateway

# Report success
echo
echo "Master node has been installed."

