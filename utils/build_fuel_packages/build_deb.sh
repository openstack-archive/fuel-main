#!/bin/bash

# This is an example how can we use docker debbuild_env to build DEB packages
# in Fuel project

set -ex

SOURCE_PATH=${HOME}/projects/fuel-main/build/packages/sources/
SPEC_PATH=${HOME}/projects/fuel-main/packages/deb/specs/
RESULT_DIR=/tmp/packages

docker run --rm -v ${SOURCE_PATH}:/opt/sandbox/SOURCES \
           -v ${SPEC_PATH}:/opt/sandbox/SPECS \
           -v ${RESULT_DIR}:/opt/sandbox/DEB \
           fuel/debbuild_env /bin/bash /opt/sandbox/build_deb_in_docker.sh
