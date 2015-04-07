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

#
# This script creates slaves node for the product, launches its installation,
# and waits for its completion
#

# Include the handy functions to operate VMs
source ./config.sh
source ./functions/vm.sh
source ./functions/network.sh

# Get variables "host_nic_name" for the slave nodes
get_fuel_name_ifaces

# Create and start slave nodes
for idx in $(eval echo {1..$cluster_size}); do
  name="${vm_name_prefix}slave-${idx}"
  vm_ram=${vm_slave_memory_mb[$idx]}
  [ -z $vm_ram ] && vm_ram=$vm_slave_memory_default
  echo
  vm_cpu=${vm_slave_cpu[$idx]}
  [ -z $vm_cpu ] && vm_cpu=$vm_slave_cpu_default
  echo
  create_vm $name "${host_nic_name[0]}" $vm_cpu $vm_ram $vm_slave_first_disk_mb

  # Add additional NICs to VM
  if [ ${#host_nic_name[*]} -gt 1 ]; then
    for nic in $(eval echo {1..$((${#host_nic_name[*]}-1))}); do
      add_hostonly_adapter_to_vm $name $((nic+1)) "${host_nic_name[${nic}]}"
    done
  fi
  # Add additional disks to VM
  echo
  add_disk_to_vm $name 1 $vm_slave_second_disk_mb
  add_disk_to_vm $name 2 $vm_slave_third_disk_mb

  enable_network_boot_for_vm $name

  # The delay required for downloading tftp boot image
  sleep 10
  start_vm $name
done

# Report success
echo
echo "Slave nodes have been created. They will boot over PXE and get discovered by the master node."
echo "To access master node, please point your browser to:"
echo "    http://${vm_master_ip}:8000/"
echo "The default username and password is admin:admin"
