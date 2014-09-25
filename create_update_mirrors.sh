#!/bin/bash -x
# Scrip will generate differential mirrors
# You can define mirror with env variable MIRROR, for example
# export MIRROR=osci-mirror-msk.msk.mirantis.net
#        or any other below:
#          osci-mirror-srt.srt.mirantis.net
#          osci-mirror-kha.kha.mirantis.net (default)
#          osci-mirror-msk.msk.mirantis.net
# you should run this script in format:
# ./create_update_mirrors.sh HIGHER_VERSION LOWER_VERSION
# for example:
# /create_update_mirrors.sh 6.0 5.1.1
# The result will be in ${RESULT_DIR}

MIRROR_HOST=${MIRROR:-osci-mirror-kha.kha.mirantis.net}

BASE_DIR=/tmp/mirrors

SUPPORTED_VERSIONS=(5.0 5.0.1 5.0.2 5.1 5.1.1 6.0)

if [ "$#" -ne 2 ]
then
  echo "Please provide two mirrors for generating difference"
  echo "Usage: $0 HIGHER_VERSION LOWER_VERSION"
  exit 1
fi

HIGHER_VERSION=$1
LOWER_VERSION=$2
RESULT_DIR=${BASE_DIR}/diff_${HIGHER_VERSION}-${LOWER_VERSION}

function is_supported_verion () {
    local array="$1[@]"
    local seeking=$2
    local in=1
    for element in "${!array}"; do
        if [[ "${element}" == "${seeking}" ]]; then
            in=0
            break
        fi
    done
    return $in
}

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

function get_mirror (){
  # Usage: $1 - mirror name
  #        $2 - version to use/get from mirror
  #        $3 - where to store result
  local HOST=${1}
  local VERSION=${2}
  local DST_DIR=${3}

  [ -d "${DST_DIR}/centos/Packages" ] || mkdir -p "${DST_DIR}/centos/Packages"
  # centos
  SRC_DIR=rsync://${HOST}/mirror/fwm/${VERSION}/centos/os/x86_64/Packages/
  rsync -avqSHP --no-perms --chmod=ugo=rwX --delete $SRC_DIR $DST_DIR/centos/Packages

  # ubuntu
  SRC_DIR=rsync://${HOST}/mirror/fwm/${VERSION}/ubuntu/pool/main/
  rsync -avqSHP --no-perms --chmod=ugo=rwX --delete $SRC_DIR $DST_DIR/ubuntu
}

# check if user provided supported versions
is_supported_verion SUPPORTED_VERSIONS ${HIGHER_VERSION} || { echo "No such version: ${HIGHER_VERSION}"; exit 1; }
is_supported_verion SUPPORTED_VERSIONS ${LOWER_VERSION} || { echo "No such version: ${LOWER_VERSION}"; exit 1; }

get_mirror "${MIRROR_HOST}" "${HIGHER_VERSION}" "${BASE_DIR}/${HIGHER_VERSION}"
get_mirror "${MIRROR_HOST}" "${LOWER_VERSION}" "${BASE_DIR}/${LOWER_VERSION}"

get_mirror_diff "${BASE_DIR}/${LOWER_VERSION}" \
  "${BASE_DIR}/${HIGHER_VERSION}" \
  "${RESULT_DIR}"

#
createrepo --verbose ${RESULT_DIR}/centos/Packages -o ${RESULT_DIR}/centos/

# ToDo: we need to discuss ubuntu(?!) packages, as we have a lot of
# warnings "is repeat but newer version"
dpkg-scanpackages ${RESULT_DIR}/ubuntu | gzip -9c > ${RESULT_DIR}/ubuntu/Packages.gz
