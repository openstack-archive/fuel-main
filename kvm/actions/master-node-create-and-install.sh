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
name="${env_name_prefix}master"
first_net="${host_net_name[`echo ${!host_net_name[*]} | cut -d " " -f 1`]}"
first_ip="${host_nic_ip[`echo ${!host_nic_ip[*]} | cut -d " " -f 1`]}"
delete_vm $name
echo

# Adding bridge NIC if any
if [[ $use_bridge == 1 ]]; then
   BRIDGE_NET="-w bridge=$br_name,model=virtio"
else
   BRIDGE_NET=""
fi

# Creating disk for master node
vm_disk_path="$(get_vm_base_path)"
disk_name="${name}_0"
disk_filename="${disk_name}.qcow2"
qemu-img create -f qcow2 -o preallocation=metadata ${vm_disk_path}/${disk_filename} ${vm_master_disk_mb}M

# Add other host-only nics to VM
HOST_NETS=""
for i in `seq 1 ${#host_net_name[*]}`
do
  HOST_NETS="$HOST_NETS -w network=${host_net_name[`echo ${!host_net_name[*]} | cut -d " " -f $i`]},model=virtio "
done

virt-install --connect qemu:///system --hvm --name $name --ram $vm_master_memory_mb --vcpus $vm_master_cpu_cores --disk "${vm_disk_path}/${disk_filename},bus=virtio,cache=none,format=qcow2,io=native" -w "network=default,mac=${mac},model=virtio" $BRIDGE_NET $HOST_NETS --autostart --graphics vnc --pxe --noautoconsole

# Start virtual machine with the master node
echo "Waiting for OS installation on Master node"
while is_vm_running $name; do
        sleep 5
done
echo "OS has been installed, rebooting the master node"
virsh destroy $name
sleep 10
virsh start $name
ssh-keygen -R $vm_master_ip
# Wait until the machine gets installed and Puppet completes its run
wait_for_product_vm_to_install $vm_master_ip $vm_master_username $vm_master_password "$vm_master_prompt"

# Report success
echo
echo "Master node has been installed."
