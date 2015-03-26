#!/bin/bash

# This is an example how can we use docker debbuild_env to build DEB packages
# in Fuel project

set -ex

PACKAGES_TO_BUILD="astute fuel-library6.1 nailgun"
SOURCE_PATH=${HOME}/test/fuel-main/build/packages/sources/
RESULT_DIR=/tmp/packages_deb

for pckgs in ${PACKAGES_TO_BUILD}; do
docker run --rm -u $UID -v ${SOURCE_PATH}/${pckgs}:/opt/sandbox/SOURCES \
           -v ${RESULT_DIR}:/opt/sandbox/DEB \
           fuel/debbuild_env /bin/bash /opt/sandbox/build_deb_in_docker.sh
done
