#!/bin/bash

# This is an example how can we use docker rpmbuild_env to build RPM packages
# in Fuel project

set -ex

SOURCE_PATH=${HOME}/projects/fuel-main/build/packages/sources
SPEC_FILE_PATH=${HOME}/projects/fuel-main/packages/rpm/specs
RESULT_DIR=/tmp/packages

rm -rf ${RESULT_DIR}
mkdir -p ${RESULT_DIR}

for pckgs in $(ls ${SOURCE_PATH}); do
docker run --rm -v ${SOURCE_PATH}/${pckgs}:/opt/sandbox/SOURCES \
           -v ${SPEC_FILE_PATH}/${pckgs}.spec:/opt/sandbox/$(basename ${pckgs}).spec \
           -v ${RESULT_DIR}:/opt/sandbox/RPMS \
           -u ${UID} \
           fuel/rpmbuild_env rpmbuild --nodeps -vv --define "_topdir /opt/sandbox" -ba /opt/sandbox/$(basename ${pckgs}).spec
done
