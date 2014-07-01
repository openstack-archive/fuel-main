#!/bin/bash

SCRIPT_PATH=$(dirname $(readlink -e $0))
UPGRADE_PATH=$SCRIPT_PATH/upgrade


error() {
  local message="$1"
  local code="${2:-1}"

  echo "${message}"

  exit "${code}"
}


function prepare_upgrade_files {
  DOCKER_IMAGES_DIR_PATH=$UPGRADE_PATH/images
  DOCKER_IMAGES_ARCHIVE_PATH=$DOCKER_IMAGES_DIR_PATH/fuel-images.tar.lrz

  pushd $DOCKER_IMAGES_DIR_PATH
  local err_msg="Failed to uncompress docker images " \
      "${DOCKER_IMAGES_ARCHIVE_PATH}, check if " \
      "you have enough free space"

  lrzuntar -f $DOCKER_IMAGES_ARCHIVE_PATH || error $err_msg
  popd
}


function run_upgrade {
  PYTHONPATH=$UPGRADE_PATH/site-packages python $UPGRADE_PATH/bin/fuel-upgrade --src $UPGRADE_PATH docker || error "Upgrade failed" $?
}


prepare_upgrade_files
run_upgrade
