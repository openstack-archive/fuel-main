#!/bin/bash
# set -x

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
# This script performs initial check and configuration of the host system. It:
#   - check that there is no previous installation of Mirantis OpenStack (if there is one, the script deletes it)

# Include the script with handy functions to operate VMs and VirtualBox networking
source ./config.sh
source ./functions/vm.sh
source ./functions/network.sh

# Delete all VMs from the previous Mirantis OpenStack installation
delete_vms_multiple $vm_name_prefix
