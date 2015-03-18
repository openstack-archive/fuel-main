#!/bin/bash

# Shutdown installation and clean environment 
./actions/prepare-environment.sh || exit 1
./actions/clean-previous-installation.sh || exit 1
