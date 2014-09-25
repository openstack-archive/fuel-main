#!/bin/bash -x

# 1. Update repo will be places in ${SROUCE}/local_mirror/ubuntu_updates/

# original repo
UBUNTU=${PWD}/local_mirror/ubuntu/pool/main
# update repo
UBUNTU_UPDATE=${PWD}/local_mirror/ubuntu_updates/pool/main

find ${UBUNTU_UPDATE} -type f -name "*.deb" -printf "%f\n" | xargs -i bash -c "test -f ${UBUNTU}{} && rm -f ${UBUNTU_UPDATE}/{}"
