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
# This script creates a master node for the product, launches its installation,
# and waits for its completion
#

# Include the handy functions to operate VMs and track ISO installation progress
source ./config.sh
source ./functions/vm.sh
source ./functions/network.sh
source ./functions/product.sh

# Create master node for the product
# Get variables "host_nic_name" for the master node
get_fuel_name_ifaces

name="${vm_name_prefix}master"

create_vm $name "${host_nic_name[0]}" $vm_master_cpu_cores $vm_master_memory_mb $vm_master_disk_mb
echo

# Add additional NICs
add_hostonly_adapter_to_vm $name 2 "${host_nic_name[1]}"

# Add NAT adapter for internet access
add_nat_adapter_to_vm $name 3 $vm_master_nat_network

# Mount ISO with installer
mount_iso_to_vm $name $iso_path

#add RDP connection
if [ ${headless} -eq 1 ]; then
  enable_vrde $name ${RDPport}
fi

if [ "$skipfuelmenu" = "yes" ]; then
  # boot_line=$(echo " vmlinuz initrd=initrd.img biosdevname=0 ks=cdrom:/ks.cfg ip=10.20.0.2 gw=10.20.0.1 dns1=10.20.0.1 netmask=255.255.255.0 hostname=fuel.domain.tld showmenu=no" | ./functions/scancodes)
   boot_line=" 39 b9 2f af 32 b2 26 a6 17 97 31 b1 16 96 2c ac 39 b9 17 97 31 b1 17 97 14 94 13 93 20 a0 0d 8d 17 97 31 b1 17 97 14 94 13 93 20 a0 34 b4 17 97 32 b2 22 a2 39 b9 30 b0 17 97 18 98 1f 9f 20 a0 12 92 2f af 31 b1 1e 9e 32 b2 12 92 0d 8d 0b 8b 39 b9 25 a5 1f 9f 0d 8d 2e ae 20 a0 13 93 18 98 32 b2 2a 27 a7 aa 35 b5 25 a5 1f 9f 34 b4 2e ae 21 a1 22 a2 39 b9 17 97 19 99 0d 8d 02 82 0b 8b 34 b4 03 83 0b 8b 34 b4 0b 8b 34 b4 03 83 39 b9 22 a2 11 91 0d 8d 02 82 0b 8b 34 b4 03 83 0b 8b 34 b4 0b 8b 34 b4 02 82 39 b9 20 a0 31 b1 1f 9f 02 82 0d 8d 02 82 0b 8b 34 b4 03 83 0b 8b 34 b4 0b 8b 34 b4 02 82 39 b9 31 b1 12 92 14 94 32 b2 1e 9e 1f 9f 25 a5 0d 8d 03 83 06 86 06 86 34 b4 03 83 06 86 06 86 34 b4 03 83 06 86 06 86 34 b4 0b 8b 39 b9 23 a3 18 98 1f 9f 14 94 31 b1 1e 9e 32 b2 12 92 0d 8d 21 a1 16 96 12 92 26 a6 34 b4 20 a0 18 98 32 b2 1e 9e 17 97 31 b1 34 b4 14 94 26 a6 20 a0 39 b9 1f 9f 23 a3 18 98 11 91 32 b2 12 92 31 b1 16 96 0d 8d 31 b1 18 98 1c 9c"
fi

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

#Sleep 10s to wait for Cobbler to settle
sleep 10
