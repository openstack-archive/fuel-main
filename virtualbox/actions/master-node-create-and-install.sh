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
create_vm $name $hostonly_interface_name $vm_master_cpu_cores $vm_master_memory_mb $vm_master_disk_mb
mount_iso_to_vm $name $iso_path

# Start virtual machine with the master node
start_vm $name

# Wait until the machine gets installed and Puppet completes its run
wait_for_product_vm_to_install $vm_master_ip $vm_master_username $vm_master_password "$vm_master_prompt"

# Report success
echo "Master node has been installed."

