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
# This script check available memory on host PC for quality provision VMs via VirtualBox
#

source ./config.sh
source ./functions/memory.sh

total_memory=$(get_available_memory)

if [ $total_memory -eq -1 ]; then
  echo "Launch without checking RAM on host PC"
  echo "Auto check memory is unavailable, you need install 'free'. Please install procps package."
else
  # Count selected RAM configuration
  for machine_number in $(eval echo {1..$cluster_size}); do
    if [ -n "${vm_slave_memory_mb[$machine_number]}" ]; then
      vm_total_mb=$(( $vm_total_mb + ${vm_slave_memory_mb[$machine_number]} ))
    else
      vm_total_mb=$(( $vm_total_mb + $vm_slave_memory_default ))
    fi
  done
  vm_total_mb=$(( $vm_total_mb + $vm_master_memory_mb ))

  # Do not run VMs if host PC not have enough RAM
  can_allocate_mb=$(( ($total_memory - 524288) / 1024 ))
  if [ $vm_total_mb -gt $can_allocate_mb ]; then
    echo "Your host has not enough memory."
    echo "You can allocate no more than ${can_allocate_mb}MB, but trying to run VMs with ${vm_total_mb}MB"
    exit 1
  fi
fi
