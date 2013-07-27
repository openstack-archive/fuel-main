#!/bin/bash 

# The number of nodes for installing OpenStack on
#   - for minimal non-HA installation, specify 2 (1 controller + 1 compute)
#   - for minimal non-HA with Cinder installation, specify 3 (1 ctrl + 1 compute + 1 cinder)
#   - for minimal HA installation, specify 4 (3 controllers + 1 compute)
cluster_size=3

# Get the first available ISO from the directory 'iso'
iso_path=`ls -1 iso/*.iso 2>/dev/null | head -1`

# Every Fuel Web machine name will start from this prefix  
vm_name_prefix=fuel-web-

# Host interfaces to bridge VMs interfaces with
idx=0
for ip in 10.20.0.1 172.16.1.1 172.16.0.1; do
  host_nic_name[$idx]=vboxnet$idx
  host_nic_ip[$idx]=$ip
  host_nic_mask[$idx]=255.255.255.0
  idx=$((idx+1))
done

# Master node settings
vm_master_cpu_cores=1
vm_master_memory_mb=1024
vm_master_disk_mb=16384

# These settings will be used to check if master node has installed or not.
# If you modify networking params for master node during the boot time
#   (i.e. if you pressed Tab in a boot loader and modified params),
#   make sure that these values reflect that change.
vm_master_ip=10.20.0.2
vm_master_username=root
vm_master_password=r00tme
vm_master_prompt='root@fuel ~]#'

# Slave node settings
vm_slave_cpu_cores=1

# This section allows you to define RAM size in MB for each slave node.
# Keep in mind that PXE boot might not work correctly with values lower than 768.
# You can specify memory size for the specific slaves, other will get default vm_slave_memory_default
vm_slave_memory_default=768
vm_slave_memory_mb[1]=768   # for controller node 768 MB should be sufficient
vm_slave_memory_mb[2]=1024  # for compute node 1GB is recommended, otherwise VM instances in OpenStack may not boot
vm_slave_memory_mb[3]=768   # for a dedicated Cinder node 768 MB should be sufficient

# This section allows you to define HDD size in MB for all the slaves nodes.
# All the slaves will have identical disk configuration. Each slave will have three disks of the following sizes.
vm_slave_first_disk_mb=16384
vm_slave_second_disk_mb=32768
vm_slave_third_disk_mb=65536
