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
    delete_vm $name
    create_vm $name ${host_nic_name[0]} ${host_nic_name[1]} ${host_nic_name[2]} $vm_slave_cpu_cores $vm_slave_memory_mb $vm_slave_disk_mb
    enable_network_boot_for_vm $name 
    start_vm $name
done

# Report success
echo "Slave nodes have been created. They will boot over PXE and get discovered by the master node."
echo "To access master node, please point your browser to:"
echo "    http://${vm_master_ip}:8000/"

