#!/bin/bash

#    Copyright 2014 Mirantis, Inc.
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
# and waits for its completion and check docker containers status
#

# Include the handy functions to operate VMs and track ISO installation progress
source config.sh
source functions/vm.sh
source functions/product.sh
source functions/containers-test.sh

# Create master node for the product
name="${vm_name_prefix}master"
create_vm $name "${host_nic_name[0]}" $vm_master_cpu_cores $vm_master_memory_mb \
          $vm_master_disk_mb
echo

# Add additional NICs
add_hostonly_adapter_to_vm $name 2 "${host_nic_name[1]}"

# Add NAT adapter for internet access
add_nat_adapter_to_vm $name 3 $vm_master_nat_network

# Mount ISO with installer
mount_iso_to_vm $name $iso_path

# Start virtual machine with the master node
echo
start_vm $name

# Wait until the machine gets installed and Puppet completes its run
wait_for_product_vm_to_install $vm_master_ip $vm_master_username \
                               $vm_master_password "$vm_master_prompt"

# Enable outbound network/internet access for the machine
enable_outbound_network_for_product_vm $vm_master_ip $vm_master_username \
          $vm_master_password "$vm_master_prompt" 3 $vm_master_nat_gateway

# Checking docker's containers
## Create test script
create_test_script $vm_master_ip $vm_master_username $vm_master_password \
                  "$vm_master_prompt"
# Check container's statuses
for container_name in nginx nailgun rabbitmq astute rsync keystone postgres \
                      rsyslog cobbler ostf mcollective;  do
    container_status $vm_master_ip $vm_master_username $vm_master_password \
                     "$vm_master_prompt" $container_name
    task_status=$?
if [[ $task_status == 1 ]]; then
          echo "Waiting for $container_name container ..."
          count=0
             while [[ $count -ne 30 ]]; do
               (( count++ ))
               echo -ne "."
               sleep 1
             done
             echo -e '\n'
          container_status $vm_master_ip $vm_master_username \
                       $vm_master_password "$vm_master_prompt" $container_name
          task_status_after_waiting=$?
               if [[ $task_status_after_waiting == 1 ]]; then
                    yellow='\e[0;33m'
                    NORMAL='\033[0m'
                     touch container-errors.log
                     echo \
                     "######################################################" \
                     >> container-errors.log
                     echo "$container_name container"
                     echo "$container_name container" >> container-errors.log
                     echo "Unable to start $container_name docker container."
                     echo "Unable to start $container_name docker container." \
                          >> container-errors.log
                     echo "Try to check it mannually by commands:"
                     echo "Try to check it mannually by commands:" \
                          >> container-errors.log
                     echo "Start container:"
                     echo "Start container:" >> container-errors.log
                     echo "dockerctl start $container_name"
                     echo "dockerctl start $container_name" \
                          >> container-errors.log
                     echo "Stop container:"
                     echo "Stop container:" >> container-errors.log
                     echo "dockerctl stop $container_name"
                     echo "dockerctl stop $container_name" \
                          >> container-errors.log
                     echo "Restart container:"
                     echo "Restart container:" >>container-errors.log
                     echo "dockerctl restart $container_name"
                     echo "dockerctl restart $container_name" \
                          >> container-errors.log
                     echo "Check container status:"
                     echo "Check container status:" >> container-errors.log
                     echo "dockerctl check $container_name"
                     echo "dockerctl check $container_name" \
                          >> container-errors.log
                     echo -e "\n" >> container-errors.log
                     echo -ne "${yellow}!!!       An error occured while "
                     echo -e "checking container(s).          !!!${NORMAL}"
                     echo -ne "${yellow}!!!  Refer to the log file "
                     echo -e "container-errors.log for details.   !!!${NORMAL}"
               fi
fi
done

# Remove test script from fuel master node
remove_test_script $vm_master_ip $vm_master_username $vm_master_password \
                   "$vm_master_prompt"

# Report success
echo
echo "Master node has been installed."

