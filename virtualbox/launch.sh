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

source ./functions/shell.sh

# Check remote host/port settings
check_remote_settings

# Add VirtualBox directory to PATH
add_virtualbox_path

echo "Prepare the host system..."
./actions/prepare-environment.sh launch || exit 1
echo

echo "Check available memory on the host system..."
./actions/check-available-memory.sh || exit 1
echo

echo "Сlean previous installation if exists..."
./actions/clean-previous-installation.sh || exit 1
echo

# Сreate host-only interfaces
./actions/create-interfaces.sh || exit 1

# Create and launch master node
./actions/master-node-create-and-install.sh || exit 1

# Create and launch slave nodes
./actions/slave-nodes-create-and-boot.sh || exit 1
