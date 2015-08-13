#!/bin/bash

# This is an example how can we use docker debbuild_env to build DEB packages
# in Fuel project, sources can be prepared by "make sources" target from fuel-main

set -ex

PACKAGES_TO_BUILD="astute fuel-library7.0 nailgun fuel-agent"
SOURCE_PATH=${HOME}/fuel-main/build/packages/sources/
RESULT_DIR=/tmp/packages_deb

rm -rf ${RESULT_DIR}
mkdir -p ${RESULT_DIR}

for pckgs in ${PACKAGES_TO_BUILD}; do
docker run --rm -u $UID -v ${SOURCE_PATH}/${pckgs}:/opt/sandbox/SOURCES \
           -v ${RESULT_DIR}:/opt/sandbox/DEB \
           fuel-7.0/debbuild_env /bin/bash /opt/sandbox/build_deb_in_docker.sh
done
