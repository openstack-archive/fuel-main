#!/bin/bash 

# The number of nodes for installing OpenStack on
#   - for minimal non-HA installation, specify 2 (1 controller + 1 compute)
#   - for minimal HA installation, specify 4 (3 controllers + 1 compute)
cluster_size=2

# Get the first available ISO from the directory 'iso'
iso_path=`ls -1 iso/*.iso 2>/dev/null | head -1`

# Every Fuel Web machine name will start from this prefix  
vm_name_prefix=fuel-web-

# This host-only interface will be created and all networking will be done throught it
hostonly_interface_name=vboxnet0
hostonly_interface_ip=10.20.0.1
hostonly_interface_mask=255.255.255.0

# Master node settings
vm_master_cpu_cores=1
vm_master_memory_mb=1024
vm_master_disk_mb=16384
vm_master_ip=10.20.0.2
vm_master_username=root
vm_master_password=r00tme
vm_master_prompt='root@nailgun ~]#'

# Slave node settings
vm_slave_cpu_cores=1
vm_slave_memory_mb=768 # PXE boot might not work with lower values  
vm_slave_disk_mb=16384

