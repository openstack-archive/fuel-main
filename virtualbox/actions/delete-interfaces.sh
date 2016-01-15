#!/bin/bash
# set -x

#    Copyright 2015 Mirantis, Inc.
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
#    This script deletes host-only network interfaces.
#

# Include scripts with handy functions to operate VMs and VirtualBox networking
source ./config.sh
source ./functions/vm.sh
source ./functions/network.sh

# Delete host-only interfaces
if [[ "${rm_network}" == "0" ]]; then
    delete_fuel_ifaces
else
    delete_all_hostonly_interfaces
fi

