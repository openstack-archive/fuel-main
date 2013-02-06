#!/bin/bash 

# Prepare the host system
./actions/prepare-environment.sh || exit 1

# Create and launch master node
./actions/master-node-create-and-install.sh || exit 1

# Create and launch slave nodes
./actions/slave-nodes-create-and-boot.sh || exit 1

