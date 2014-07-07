#!/bin/bash

SCRIPT_PATH=$(dirname $(readlink -e $0))
UPGRADE_PATH=$SCRIPT_PATH/upgrade
UPGRADERS={{UPGRADERS}}


function error {
  local message="$1"
  local code="${2:-1}"

  echo "${message}"

  exit "${code}"
}


function prepare_upgrade_files {
  DOCKER_IMAGES_DIR_PATH=$UPGRADE_PATH/images
  DOCKER_IMAGES_ARCHIVE_PATH=$DOCKER_IMAGES_DIR_PATH/fuel-images.tar.lrz

  pushd $DOCKER_IMAGES_DIR_PATH
  lrzuntar -f $DOCKER_IMAGES_ARCHIVE_PATH
  popd
}


function run_upgrade {
  # decompress images iff the docker upgrader is used
  if [[ $UPGRADERS == *docker* ]]; then
    prepare_upgrade_files
  fi

  # run fuel_upgrade script
  PYTHONPATH="$UPGRADE_PATH/site-packages" python "$UPGRADE_PATH/bin/fuel-upgrade" --src "$UPGRADE_PATH" $UPGRADERS "$@" || error "Upgrade failed" $?
}


run_upgrade "$@"
