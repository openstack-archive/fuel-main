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

# Add VirtualBox directory to PATH
case "$(uname)" in
    CYGWIN*)
        vbox_path_registry=`cat /proc/registry/HKEY_LOCAL_MACHINE/SOFTWARE/Oracle/VirtualBox/InstallDir`
        vbox_path=`cygpath "$vbox_path_registry"| sed -e 's%/$%%'`
        export PATH=$PATH:$vbox_path
      ;;
    *)
      ;;
esac

# Prepare the host system
./actions/prepare-environment.sh || exit 1

# Check available memory on the host system
./actions/check-available-memory.sh || exit 1

# Сlean previous installation if exists
./actions/clean-previous-installation.sh || exit 1

# Сreate host-only interfaces
./actions/create-interfaces.sh || exit 1

# Create and launch master node
./actions/master-node-create-and-install.sh || exit 1

# Create and launch slave nodes
./actions/slave-nodes-create-and-boot.sh || exit 1
