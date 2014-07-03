#!/bin/bash

SCRIPT_PATH=$(dirname $(readlink -e $0))
UPGRADE_PATH=$SCRIPT_PATH/upgrade

function prepare_upgrade_files {
  DOCKER_IMAGES_DIR_PATH=$UPGRADE_PATH/images
  DOCKER_IMAGES_ARCHIVE_PATH=$DOCKER_IMAGES_DIR_PATH/fuel-images.tar.lrz

  pushd $DOCKER_IMAGES_DIR_PATH
  lrzuntar -f $DOCKER_IMAGES_ARCHIVE_PATH
  popd
}

function run_upgrade {
  PYTHONPATH=$UPGRADE_PATH/site-packages python $UPGRADE_PATH/bin/fuel-upgrade --src $UPGRADE_PATH docker
}

prepare_upgrade_files
run_upgrade
