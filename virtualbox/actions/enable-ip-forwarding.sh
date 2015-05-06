#!/bin/bash

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
# This script performs initial check and configuration IP forwarding on the
# host system.
#

source ./config.sh

if [[ "$(uname)" == "Linux" || "$(uname)" == "Darwin" ]]; then
    # Reset timestamp sudo
    sudo -k
    echo -e "To configure NAT and Firewall, the script requires the sudo password"
    current_dir=$(pwd)
    sudo $current_dir/actions/add-firewall-rules.sh $fuel_master_ips
elif [ "$(uname -s | cut -c1-6)" != "CYGWIN" ]; then
    echo "$(uname) is not supported operating system."
    exit 1
fi
