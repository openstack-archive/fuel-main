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
source ./functions/translate.sh

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
  cmdline="$(grep 'append initrd' ../iso/isolinux/isolinux.cfg -m1 2> /dev/null | sed -e 's/^[ ]*append//')"
  cmdline="${cmdline:- initrd=initrd.img net.ifnames=0 biosdevname=0 ks=hd:sr0:/ks.cfg ip=10.20.0.2::10.20.0.1:255.255.255.0:fuel.domain.tld:eth0:off::: dns1=10.20.0.1 selinux=0}"
  boot_line="$(translate "$cmdline showmenu=no"$'\n')"
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
