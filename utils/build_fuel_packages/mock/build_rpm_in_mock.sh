#!/bin/bash

set -ex

# mock configuration
CENTOS_ARCH=x86_64
CONFIG_DIR=$PWD/configs
PRODUCT_VERSION=7.0
RESULT_DIR=$PWD/logs

# build configuration
PACKAGES_TO_BUILD="astute fuel-library${PRODUCT_VERSION} fuel-main fuel-ostf nailgun python-fuelclient"
SOURCE_PATH=${HOME}/test/fuel-main/build/packages/sources
SPEC_FILE_PATH=${HOME}/test/fuel-main/build/repos

rm -rf ${RESULT_DIR}
mkdir -p ${RESULT_DIR}

if [[ $1 == "--with-init" ]]; then
  # clean-up everything, if any exists
  /usr/bin/mock --configdir=${CONFIG_DIR} -r fuel-${PRODUCT_VERSION}-x86_64 --scrub=all

  # init env
  /usr/bin/mock --configdir=${CONFIG_DIR} -v \
    -r fuel-${PRODUCT_VERSION}-${CENTOS_ARCH} --init \
    --resultdir ${RESULT_DIR}
fi

  # build SRPM
for pkg in ${PACKAGES_TO_BUILD}; do
  /usr/bin/mock -v --configdir=${CONFIG_DIR} \
    -r fuel-${PRODUCT_VERSION}-${CENTOS_ARCH} \
    --spec=${SPEC_FILE_PATH}/${pkg}/specs/${pkg}.spec \
    --sources=${SOURCE_PATH}/${pkg} \
    --no-clean --no-cleanup-after \
    --buildsrpm \
    --resultdir ${RESULT_DIR}
done

  # build RPM
for srpm in $(ls ${RESULT_DIR}/*src.rpm); do
  /usr/bin/mock -v --configdir=${CONFIG_DIR} \
    -r fuel-${PRODUCT_VERSION}-${CENTOS_ARCH} \
    --no-clean --no-cleanup-after \
    ${srpm} \
    --resultdir ${RESULT_DIR}
done
