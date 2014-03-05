#!/bin/bash
# set -x

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
# This script performs initial check and configuration of the host system. It:
#   - creates host-only network interfaces
#

# Include the script with handy functions to operate VMs and VirtualBox networking
source config.sh 
source functions/vm.sh
source functions/network.sh

# Delete all host-only interfaces
delete_all_hostonly_interfaces

# Create the required host-only interfaces
# Change {0..2} to {0..4} below if you are going to create 5 interfaces instead of 3
for idx in $(eval echo {0..2}); do
  create_hostonly_interface "${host_nic_name[$idx]}" ${host_nic_ip[$idx]} ${host_nic_mask[$idx]}
done
