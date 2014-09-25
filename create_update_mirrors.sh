#!/bin/bash -x

# find part can be implemented in function

function synchro (){
  # this function will result UPDATE folder, which is: NEW - OLD = UPDATE
  # compare only by filename
  FNAME=$1
  NEW=$2
  OLD=$3
  UPDATE=$4
  find "${NEW}" -type f -name "${FNAME}" -printf "%f\n" | xargs -i bash -c "test -f ${OLD}/{} || cp -v ${NEW}/{} ${UPDATE}/{}"
}

################################## CENTOS
# version 5.1
CENTOS_OLD=/tmp/UBUNTU/fuel-main-5.1/local_mirror/centos/os/x86_64/Packages
# latest version
CENTOS_NEW=/tmp/UBUNTU/fuel-main-6.0/local_mirror/centos/os/x86_64/Packages
# update mirror
CENTOS_UPDATE_ROOT=/tmp/UBUNTU/centos_update
CENTOS_UPDATE=${CENTOS_UPDATE_ROOT}/os/x86_64/Packages

rm -rf ${CENTOS_UPDATE_ROOT}
mkdir -p ${CENTOS_UPDATE}

synchro "*.rpm" "${CENTOS_NEW}" "${CENTOS_OLD}" "${CENTOS_UPDATE}"

createrepo --verbose ${CENTOS_UPDATE}/ -o ${CENTOS_UPDATE}/../

################################### UBUNTU
# version 5.1
UBUNTU_OLD=/tmp/UBUNTU/fuel-main-5.1/local_mirror/ubuntu/pool/main
# latest version
UBUNTU_NEW=/tmp/UBUNTU/fuel-main-6.0/local_mirror/ubuntu/pool/main
# update mirror
UBUNTU_UPDATE_ROOT=/tmp/UBUNTU/ubuntu_update
UBUNTU_UPDATE=${UBUNTU_UPDATE_ROOT}/pool/update

rm -rf ${UBUNTU_UPDATE_ROOT}
mkdir -p ${UBUNTU_UPDATE}

synchro "*.deb" "${UBUNTU_NEW}" "${UBUNTU_OLD}" "${UBUNTU_UPDATE}"

# use flat mirror declaration
dpkg-scanpackages ${UBUNTU_UPDATE} | gzip -9c > ${UBUNTU_UPDATE}/../Packages.gz
