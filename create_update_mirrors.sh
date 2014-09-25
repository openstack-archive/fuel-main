#!/bin/bash
# Scrip will generate differential mirrors
#
# The list of env variable that can be used:
# - MIRROR - mirror host, for example:
#   export MIRROR=osci-mirror-msk.msk.mirantis.net
#        or any other mirror below:
#          osci-mirror-srt.srt.mirantis.net
#          osci-mirror-kha.kha.mirantis.net (default)
#          osci-mirror-msk.msk.mirantis.net
# - OUTPUT_DIR - where to store result (default /tmp/mirrors)
# - DEBUG - run in verbose mode
#
# you should run this script in format:
# ./create_update_mirrors.sh HIGHER_VERSION LOWER_VERSION
#   for example:
#     ./create_update_mirrors.sh 6.0 5.1.1
#     ./create_update_mirrors.sh /PATH/TO/LOCAL/MIRROR 5.0
# The result will be in ${BASE_DIR}

test -z ${DEBUG} || set -x

MIRROR_HOST=${MIRROR:-osci-mirror-kha.kha.mirantis.net}
BASE_DIR=${OUTPUT_DIR:-/tmp/mirrors}

if [ "$#" -ne 2 ]
then
  echo "Please provide two mirrors for generating difference"
  echo "Usage: $0 HIGHER_VERSION LOWER_VERSION"
  exit 1
fi

HIGHER_VERSION=$1
LOWER_VERSION=$2
HV_DIR=${BASE_DIR}/${HIGHER_VERSION}
LV_DIR=${BASE_DIR}/${LOWER_VERSION}

function get_mirror_diff (){
  # Usage: $1 - older version
  #        $2 - newer version
  #        $3 - diff/result dir
  local OLDER=$1
  local NEWER=$2
  local DIFF=$3
  rsync -avrqSHP --compare-dest=${OLDER} \
    ${NEWER}/ \
    ${DIFF}
}

function get_mirror() {
  # SRC
  # DST
  local SRC_PATH=${1}
  local DST_DIR_CENTOS=${2}/centos/os/x86_64/Packages
  local DST_DIR_UBUNTU=${2}/ubuntu/pool/main/

  # centos
  [ -d "${DST_DIR_CENTOS}" ] || mkdir -p "${DST_DIR_CENTOS}"
  SRC_DIR=${SRC_PATH}/centos/os/x86_64/Packages/
  rsync -avqSHP --no-perms --chmod=ugo=rwX --delete $SRC_DIR $DST_DIR_CENTOS

  # ubuntu
  [ -d "${DST_DIR_UBUNTU}" ] || mkdir -p "${DST_DIR_UBUNTU}"
  SRC_DIR=${SRC_PATH}/ubuntu/pool/main/
  rsync -avqSHP --no-perms --chmod=ugo=rwX --delete $SRC_DIR $DST_DIR_UBUNTU
}

# user can provide local path, so we don't need to download mirror
if [[ ${HIGHER_VERSION:0:1} == '/' ]]; then
  # user provided local path
  test -d ${HIGHER_VERSION} || { echo "Please, be sure that the folder ${HIGHER_VERSION} exists"; exit 1; }
  get_mirror "${HIGHER_VERSION}" "${HV_DIR}"
  # change version value to local_path
  HIGHER_VERSION=local_path
else
  # need to download from mirror
  get_mirror "rsync://${MIRROR_HOST}/mirror/fwm/${HIGHER_VERSION}" "${HV_DIR}"
fi

if [[ ${LOWER_VERSION:0:1} == '/' ]]; then
  # user provided local path
  test -d ${LOWER_VERSION} || { echo "Please, be sure that the folder ${LOWER_VERSION} exists"; exit 1; }
  get_mirror "${LOWER_VERSION}" "${LV_DIR}"
  # change version value to local_path
  LOWER_VERSION=local_path
else
  get_mirror "rsync://${MIRROR_HOST}/mirror/fwm/${LOWER_VERSION}" "${LV_DIR}"
fi

RESULT_DIR=${BASE_DIR}/diff_${HIGHER_VERSION}-${LOWER_VERSION}

get_mirror_diff "${LV_DIR}" \
  "${HV_DIR}" \
  "${RESULT_DIR}"

createrepo ${RESULT_DIR}/centos/os/x86_64/Packages -o ${RESULT_DIR}/centos/os/x86_64/

# ToDo: we need to discuss ubuntu(?!) packages, as we have a lot of
# warnings "is repeat but newer version" but mainly for old versions
dpkg-scanpackages -m ${RESULT_DIR}/ubuntu/pool/main | gzip -9c > ${RESULT_DIR}/ubuntu/pool/Packages.gz
