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
for ip in 10.20.0.1 240.0.1.1 172.16.0.1; do
  host_nic_name[$idx]=vboxnet$idx
  host_nic_ip[$idx]=$ip
  host_nic_mask[$idx]=255.255.255.0
  idx=$((idx+1))
done

# Master node settings
vm_master_cpu_cores=1
vm_master_memory_mb=1024
vm_master_disk_mb=16384
vm_master_ip=10.20.0.2
vm_master_username=root
vm_master_password=r00tme
vm_master_prompt='root@fuelweb ~]#'

# Slave node settings
vm_slave_cpu_cores=1
vm_slave_memory_mb[1]=768   # PXE boot might not work with lower values
vm_slave_memory_mb[2]=1024  # VM in OpenStack may not not boot with lower values, use this for Compute
vm_slave_memory_mb[3]=768   # If not specified, 768Mb is default
vm_slave_disk_mb=16384
vm_slave_disk2_mb=512000
vm_slave_disk3_mb=2300000

