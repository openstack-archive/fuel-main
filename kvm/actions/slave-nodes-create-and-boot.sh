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
    name="${env_name_prefix}slave-${idx}"
    echo
    delete_vm $name
    vm_ram=${vm_slave_memory_mb[$idx]}
    [ -z $vm_ram ] && vm_ram=$vm_slave_memory_default
    echo
    first_net="default"
    create_vm $name $first_net $vm_slave_cpu_cores $vm_ram $vm_slave_first_disk_mb

    # Add additional NICs to VM
    echo

    # Adding bridge NIC if any
    if [[ $use_bridge == 1 ]]; then
      add_br_nic_to_vm $name $br_name
    fi

    # Add other host-only nics to VM

    for i in `seq 1 ${#host_net_name[*]}`
    do
      add_nic_to_vm $name ${host_net_name[`echo ${!host_net_name[*]} | cut -d " " -f $i`]}
    done

    # Add additional disks to VM
    echo
    add_disk_to_vm $name 1 $vm_slave_second_disk_mb
    #add_disk_to_vm $name 2 $vm_slave_third_disk_mb

    #enable_network_boot_for_vm $name
    start_vm $name
done

# Report success
echo
echo "Slave nodes have been created. They will boot over PXE and get discovered by the master node."
echo "To access master node, please point your browser to:"
echo "    http://${vm_master_ip}:8000/"
