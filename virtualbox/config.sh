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

# Get the first available ISO from the directory 'iso'
iso_path=`ls -1t iso/*.iso 2>/dev/null | head -1`

# Every Mirantis OpenStack machine name will start from this prefix
vm_name_prefix=fuel-

# Host interfaces to bridge VMs interfaces with
# VirtualBox has different virtual NIC naming convention and index base
# between Windows and Linux/MacOS
idx=0
# Please add the IPs accordingly if you going to create non-default NICs number
# 10.20.0.1/24   - Mirantis OpenStack Admin network
# 172.16.0.1/24  - OpenStack Public/External/Floating network
# 172.16.1.1/24  - OpenStack Fixed/Internal/Private network
# 192.168.0.1/24 - OpenStack Management network
# 192.168.1.1/24 - OpenStack Storage network (for Ceph, Swift etc)
for ip in 10.20.0.1 172.16.0.1 172.16.1.1 ; do
# VirtualBox for Windows has different virtual NICs naming and indexing
  case "$(uname)" in
    Linux)
      host_nic_name[$idx]=vboxnet$idx
      os_type="linux"
    ;;
    Darwin)
      host_nic_name[$idx]=vboxnet$idx
      os_type="darwin"
    ;;
    CYGWIN*)
      if [ $idx -eq 0 ]; then
        host_nic_name[$idx]='VirtualBox Host-Only Ethernet Adapter'
      else
        host_nic_name[$idx]='VirtualBox Host-Only Ethernet Adapter #'$((idx+1))
      fi
      os_type="cygwin"
    ;;
    *)
      echo "$(uname) is not supported operating system."
      exit 1
    ;;
  esac
  host_nic_ip[$idx]=$ip
  host_nic_mask[$idx]=255.255.255.0
  idx=$((idx+1))
done

# Master node settings
vm_master_cpu_cores=1
vm_master_memory_mb=1536
vm_master_disk_mb=65535

# Master node access to the internet through the host system, using VirtualBox NAT adapter
vm_master_nat_network=192.168.200/24
vm_master_nat_gateway=192.168.200.2

# These settings will be used to check if master node has installed or not.
# If you modify networking params for master node during the boot time
#   (i.e. if you pressed Tab in a boot loader and modified params),
#   make sure that these values reflect that change.
vm_master_ip=10.20.0.2
vm_master_username=root
vm_master_password=r00tme
vm_master_prompt='root@fuel ~]#'


# Check available commands and RAM on host PC
if [ "$os_type" = "linux" ]; then
  # runing on linux
  if [ "$(which free)" != "" ]; then
    # using free
    total_memory=$(free | grep Mem | awk '{print $2}')
  elif [ $(which top) != '' ]; then
    # using top
    total_memory=$(top -n 1 | grep "Mem:" | awk '{ print $4 }')
  else
    total_memory="-1"
  fi
elif [ "$os_type" = "darwin" ]; then
  # runing on mac os darwin
  if [ "$(which sysctl)" != "" ]; then
    # using sysctl
    total_memory=$(sysctl -n hw.memsize)
  else
    total_memory="-1"
  fi
elif [ "$os_type" = "cygwin" ]; then
  # runing on cygwin
  if [ "$(which free)" != "" ]; then
    # using free
    total_memory=$(free | grep Mem | awk '{print $2}')
  elif [ $(which top) != '' ]; then
    # using top
    total_memory=$(top -n 1 | grep "Mem:" | awk '{ print $4 }')
  else
    total_memory="-1"
  fi
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


# Apply of different default configurations depending on the available memory
# 4GB: 1 admin node with 1.5GB, 2 cluster node with 1GB RAM ~ 3GB
# 6GB: 1 admin node with 1.5GB, 2 cluster node with 1.5GB RAM ~ 4.5GB
# 8GB: 1 admin node with 1.5GB, 3 cluster node with 1.5GB ~ 5.5GB
# 12GB: 1 admin node with 1.5GB, 4 cluster node with 2GB ~ 9.5GB
# 16GB: 1 admin node with 1.5GB, 5 cluster node with 2GB ~ 11.5GB
total_memory=3145728
if [ $total_memory -gt 12582912 ]; then
  # For host with 16GB RAM
  cluster_size=5
  vm_slave_memory_default=2048
elif [ $total_memory -gt 8388608 ]; then
  # For host with 12GB RAM
  cluster_size=4
  vm_slave_memory_default=2048
elif [ $total_memory -gt 6291456 ]; then
  # For host with 8GB RAM
  cluster_size=3
  vm_slave_memory_default=1536
elif [ $total_memory -gt 4194304 ]; then
  # For host with 6GB RAM
  cluster_size=2
  vm_slave_memory_default=1536
elif [ $total_memory -gt 3145728 ]; then
  # For host with 4GB RAM
  cluster_size=2
  vm_slave_memory_default=1024
else
  echo "You host PC no have enough memory."
  exit 1
fi

#
# Manual configuration cluster parameters
#

# The number of nodes for installing OpenStack on
#   - for minimal non-HA installation, specify 2 (1 controller + 1 compute)
#   - for minimal non-HA with Cinder installation, specify 3 (1 ctrl + 1 compute + 1 cinder)
#   - for minimal HA installation, specify 4 (3 controllers + 1 compute)
# Default recommended configuration
# cluster_size=2 # - 4GB non-HA, 1 controller, 1 compute
# cluster_size=2 # - 6GB non-HA, 1 controller, 1 compute
# cluster_size=3 # - 8GB non-HA, 1 controller, 3 compute/cinder nodes
# cluster_size=4 # - 12GB HA, 3 controller, 1 compute/cinder nodes
# cluster_size=5 # - 16Gb HA, 3 controllers, 1 compute, 1 cinder

# Slave node settings. This section allows you to define CPU count for each slave node.
# vm_slave_cpu_default=1
# You can specify CPU count for your nodes as you wish, but keep in mind resources of your machine.
# If you don't, then will be used default parameter
# vm_slave_cpu[1]=1
# vm_slave_cpu[2]=1
# vm_slave_cpu[3]=1


# This section allows you to define RAM size in MB for each slave node.
# Keep in mind that PXE boot might not work correctly with values lower than 768.
# You can specify memory size for the specific slaves, other will get default vm_slave_memory_default
# Mirantis OpenStack 3.2 controllers require 1280 MiB of RAM as absolute minimum due to Heat!

# vm_slave_memory_mb[1]=2048
# vm_slave_memory_mb[2]=1024  # for compute node 1GB is recommended, otherwise VM instances in OpenStack may not boot
# vm_slave_memory_mb[3]=1024  # for dedicated Cinder, 768Mb is OK, but Ceph needs 1Gb minimum


# Count selected RAM configuration
for machine_number in $(eval echo {1..$cluster_size}); do
  if [ -n ${vm_slave_memory_mb[$machine_number]} ]; then
    vm_total_mb=$(( $vm_total_mb + ${vm_slave_memory_mb[$machine_number]} ))
  else
    vm_total_mb=$(( $vm_total_mb + $vm_slave_memory_default ))
  fi
done
vm_total_mb=$(( $vm_total_mb + $vm_master_memory_mb ))

# Do not run VMs if host PC not have enough RAM
can_allocate_mb=$(( ($total_memory - 524288) / 1024 ))
if [ $vm_total_mb -gt $can_allocate_mb ]; then
  echo "You host not have anought memory"
  echo "You can allocate ${can_allocate_mb}MB, but try run VMs with ${vm_total_mb}MB total RAM"
  exit 1
fi
