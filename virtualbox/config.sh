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

source ./functions/memory.sh

# Get the first available ISO from the directory 'iso'
iso_path=`ls -1t iso/*.iso 2>/dev/null | head -1`

# Every Mirantis OpenStack machine name will start from this prefix
vm_name_prefix=fuel-

# By default, all available network interfaces vboxnet won't be removed,
# if their IP addresses don't match with fuel_master_ips (10.20.0.1 172.16.0.254
# 172.16.1.1)
# If you want to remove all existing vbox interfaces, then use rm_network=1
# 0 - don't remove all vbox networks. Remove only fuel networks if they exist
# 1 - remove all vbox networks
rm_network=0

# Please add the IPs accordingly if you going to create non-default NICs number
# 10.20.0.1/24   - Mirantis OpenStack Admin network
# 172.16.0.1/24  - OpenStack Public/External/Floating network
# 172.16.1.1/24  - OpenStack Fixed/Internal/Private network
# 192.168.0.1/24 - OpenStack Management network
# 192.168.1.1/24 - OpenStack Storage network (for Ceph, Swift etc)
fuel_master_ips="10.20.0.1 172.16.0.254 172.16.1.1"

# Network mask for fuel interfaces
mask="255.255.255.0"

# Determining the type of operating system and adding CPU core to the master node
  case "$(uname)" in
    Linux)
      os_type="linux"
      if [ "$(nproc)" -gt "1" ]; then
        vm_master_cpu_cores=2
      else
        vm_master_cpu_cores=1
      fi
    ;;
    Darwin)
      os_type="darwin"
      mac_nproc=`sysctl -a | grep machdep.cpu.thread_count | sed 's/^machdep.cpu.thread_count\:[ \t]*//'`
      if [ "$mac_nproc" -gt "1" ]; then
        vm_master_cpu_cores=2
      else
        vm_master_cpu_cores=1
      fi
    ;;
    CYGWIN*)
      os_type="cygwin"
      if [ "$(nproc)" -gt "1" ]; then
        vm_master_cpu_cores=2
      else
        vm_master_cpu_cores=1
      fi
    ;;
    *)
      echo "$(uname) is not supported operating system."
      exit 1
    ;;
  esac

# Master node settings
vm_master_memory_mb=1536
vm_master_disk_mb=65535

# Master node access to the internet through the host system, using VirtualBox NAT adapter
vm_master_nat_network=192.168.200.0/24
vm_master_nat_gateway=192.168.200.2

# These settings will be used to check if master node has installed or not.
# If you modify networking params for master node during the boot time
#   (i.e. if you pressed Tab in a boot loader and modified params),
#   make sure that these values reflect that change.
vm_master_ip=10.20.0.2
vm_master_username=root
vm_master_password=r00tme
vm_master_prompt='root@fuel ~]#'

# The number of nodes for installing OpenStack on
#   - for minimal non-HA installation, specify 2 (1 controller + 1 compute)
#   - for minimal non-HA with Cinder installation, specify 3 (1 ctrl + 1 compute + 1 cinder)
#   - for minimal HA installation, specify 4 (3 controllers + 1 compute)
if [ "$CONFIG_FOR" = "16GB" ]; then
  cluster_size=5
elif [ "$CONFIG_FOR" = "8GB" ]; then
  cluster_size=3
else
  # Section for custom configuration
  cluster_size=3
fi

# Slave node settings. This section allows you to define CPU count for each slave node.

# You can specify CPU count for your nodes as you wish, but keep in mind resources of your machine.
# If you don't, then will be used default parameter
if [ "$CONFIG_FOR" = "16GB" ]; then
  vm_slave_cpu_default=1

  vm_slave_cpu[1]=1
  vm_slave_cpu[2]=1
  vm_slave_cpu[3]=1
  vm_slave_cpu[4]=1
  vm_slave_cpu[5]=1
elif [ "$CONFIG_FOR" = "8GB" ]; then
  vm_slave_cpu_default=1

  vm_slave_cpu[1]=1
  vm_slave_cpu[2]=1
  vm_slave_cpu[3]=1
else
  # Section for custom configuration
  vm_slave_cpu_default=1

  vm_slave_cpu[1]=1
  vm_slave_cpu[2]=1
  vm_slave_cpu[3]=1
fi

# This section allows you to define RAM size in MB for each slave node.
# Keep in mind that PXE boot might not work correctly with values lower than 768.
# You can specify memory size for the specific slaves, other will get default vm_slave_memory_default
# Mirantis OpenStack 3.2 controllers require 1280 MiB of RAM as absolute minimum due to Heat!

# You may comment out all the following memory parameters to use default value for each node.
# It is recommended if you going to try HA configurations.
# for controller node at least 1.5Gb is required if you also run Ceph and Heat on it
# and for Ubuntu controller we need 2Gb of ram

# For compute node 1GB is recommended, otherwise VM instances in OpenStack may not boot
# For dedicated Cinder, 768Mb is OK, but Ceph needs 1Gb minimum

if [ "$CONFIG_FOR" = "16GB" ]; then
  vm_slave_memory_default=1536

  vm_slave_memory_mb[1]=2048
  vm_slave_memory_mb[2]=2048
  vm_slave_memory_mb[3]=2048
  vm_slave_memory_mb[4]=2048
  vm_slave_memory_mb[5]=2048
elif [ "$CONFIG_FOR" = "8GB" ]; then
  vm_slave_memory_default=1024

  vm_slave_memory_mb[1]=1536
  vm_slave_memory_mb[2]=1536
  vm_slave_memory_mb[3]=1536
else
  # Section for custom configuration
  vm_slave_memory_default=1024

  vm_slave_memory_mb[1]=2048
  vm_slave_memory_mb[2]=1024
  vm_slave_memory_mb[3]=1024
fi

# Within demo cluster created by this script, all slaves (controller
# and compute nodes) will have identical disk configuration. Each
# slave will have three disks with sizes defined by the variables below. In a disk configuration
# dialog you will be able to allocate the whole disk or it's part for
# operating system (Base OS), VMs (Virtual Storage), Ceph or other function,
# depending on the roles applied to the server.
# Nodes with combined roles may require more disk space.
vm_slave_first_disk_mb=65535
vm_slave_second_disk_mb=65535
vm_slave_third_disk_mb=65535

# Set to 1 to run VirtualBox in headless mode
headless=0
skipfuelmenu="no"
