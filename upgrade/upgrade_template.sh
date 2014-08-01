#!/bin/bash

SCRIPT_PATH=$(dirname $(readlink -e $0))
UPGRADE_PATH=$SCRIPT_PATH/upgrade
UPGRADERS=${UPGRADERS:-{{UPGRADERS}}}
LOCK_FILE=/var/lock/fuel_upgarde.lock


function error {
  local message="$1"
  local code="${2:-1}"

  echo "${message}"

  exit "${code}"
}


function prepare_upgrade_files {
  DOCKER_IMAGES_DIR_PATH=$UPGRADE_PATH/images
  DOCKER_IMAGES_ARCHIVE_PATH=$DOCKER_IMAGES_DIR_PATH/fuel-images.tar.lrz

  pushd $DOCKER_IMAGES_DIR_PATH >> /dev/null

  local err_msg="Failed to uncompress docker "\
"images ${DOCKER_IMAGES_ARCHIVE_PATH}, check "\
"if you have enough free space"

  lrzuntar -f $DOCKER_IMAGES_ARCHIVE_PATH || error "$err_msg"

  popd >> /dev/null
}


function run_upgrade {
  # decompress images iff the docker upgrader is used
  if [[ $UPGRADERS == *docker* ]]; then
    prepare_upgrade_files
  fi

  # run fuel_upgrade script
  PYTHONPATH="$UPGRADE_PATH/site-packages" python "$UPGRADE_PATH/bin/fuel-upgrade" --src "$UPGRADE_PATH" $UPGRADERS "$@" || error "Upgrade failed" $?
}


if [ "$1" == "--version" ]; then
  cat $UPGRADE_PATH/config/version.yaml
  exit
fi

(flock -n 9 || error "Upgrade is already running. Lock file: ${LOCK_FILE}"
    run_upgrade "$@"
) 9> $LOCK_FILE
