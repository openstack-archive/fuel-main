#!/bin/bash 

#
# This script can be used as a handly utility to provide master node with the internet access
# It configures network interface inside the VM which is mapped to VirtualBox NAT adapter, and
# also configures default gateway.
#
# Typically, you would use this script after time after rebooting VirtualBox VM with the master node.

# Include the handy functions to operate VMs and track ISO installation progress
source config.sh
source functions/vm.sh
source functions/product.sh

# Master node name
name="${vm_name_prefix}master"

# Enable outbound network/internet access for the machine
enable_outbound_network_for_product_vm $vm_master_ip $vm_master_username $vm_master_password "$vm_master_prompt" 3 $vm_master_nat_gateway

