#!/bin/bash 

#
# This script creates slaves node for the product, launches its installation,
# and waits for its completion
#

# Include the handy functions to operate VMs
source config.sh
source functions/vm.sh

# Create and start slave nodes
for idx in $(seq 1 $cluster_size); do
    name="${vm_name_prefix}slave-${idx}"
    echo
    delete_vm $name
    vm_ram=${vm_slave_memory_mb[$idx]}
    [ -z $vm_ram ] && vm_ram=$vm_slave_memory_default
    echo
    create_vm $name ${host_nic_name[0]} $vm_slave_cpu_cores $vm_ram $vm_slave_first_disk_mb

    # Add additional NICs to VM
    echo
    add_nic_to_vm $name 2 ${host_nic_name[1]}
    add_nic_to_vm $name 3 ${host_nic_name[2]}

    # Add additional disks to VM
    echo
    add_disk_to_vm $name 1 $vm_slave_second_disk_mb
    add_disk_to_vm $name 2 $vm_slave_third_disk_mb

    enable_network_boot_for_vm $name 
    start_vm $name
done

# Report success
echo
echo "Slave nodes have been created. They will boot over PXE and get discovered by the master node."
echo "To access master node, please point your browser to:"
echo "    http://${vm_master_ip}:8000/"

