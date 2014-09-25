#!/bin/bash -x

# find part can be implemented in function

################################## CENTOS
# version 5.1
CENTOS_OLD=/tmp/UBUNTU/fuel-main-5.1/local_mirror/centos/os/x86_64/Packages/
# latest version
CENTOS_NEW=/tmp/UBUNTU/fuel-main-6.0/local_mirror/centos/os/x86_64/Packages/
# update mirror
CENTOS_UPDATE_ROOT=/tmp/UBUNTU/centos_update
CENTOS_UPDATE=${CENTOS_UPDATE_ROOT}/os/x86_64/Packages/

rm -rf ${CENTOS_UPDATE_ROOT}
mkdir -p ${CENTOS_UPDATE}

find ${CENTOS_NEW} -type f -name "*.rpm" -printf "%f\n" | xargs -i bash -c "test -f ${CENTOS_OLD}/{} || cp -v ${CENTOS_NEW}/{} ${CENTOS_UPDATE}/{}"

createrepo --verbose ${CENTOS_UPDATE}/ -o ${CENTOS_UPDATE}/../

################################### UBUNTU
# version 5.1
UBUNTU_OLD=/tmp/UBUNTU/fuel-main-5.1/local_mirror/ubuntu/pool/main/
# latest version
UBUNTU_NEW=/tmp/UBUNTU/fuel-main-6.0/local_mirror/ubuntu/pool/main/
# update mirror
UBUNTU_UPDATE_ROOT=/tmp/UBUNTU/ubuntu_update
UBUNTU_UPDATE=${UBUNTU_UPDATE_ROOT}/pool/update

rm -rf ${UBUNTU_UPDATE_ROOT}
mkdir -p ${UBUNTU_UPDATE}

find ${UBUNTU_NEW} -type f -name "*.deb" -printf "%f\n" | xargs -i bash -c "test -f ${UBUNTU_OLD}/{} || cp -v ${UBUNTU_NEW}/{} ${UBUNTU_UPDATE}/{}"

reprepro includedeb precise ${UBUNTU_UPDATE}/*
