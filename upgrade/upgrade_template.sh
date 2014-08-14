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


function run_upgrade {
  # run fuel_upgrade script
  PYTHONPATH="$UPGRADE_PATH/site-packages" python "$UPGRADE_PATH/bin/fuel-upgrade" --src "$UPGRADE_PATH" $UPGRADERS "$@" || error "Upgrade failed" $?
}


function switch_to_version {
  version=$1
  version_path=/etc/fuel/$version/version.yaml

  if [ ! -f $version_path ]; then
    error "Version ${version} not found"
  fi

  # Replace symlink to current version
  ln -sf $version_path /etc/fuel/version.yaml
  # Replace symlink to supervisor scripts
  ln -nsf /etc/supervisord.d/$version /etc/supervisord.d/current
  # Stop all supervisor services
  supervisorctl stop all &
  # And at the same time stop all docker containers
  docker stop -t=4 $(docker ps -q)
  # Restart supervisor
  service supervisord restart
  exit
}


function show_version {
  cat $UPGRADE_PATH/config/version.yaml
  exit
}


function upgrade {
  (flock -n 9 || error "Upgrade is already running. Lock file: ${LOCK_FILE}"
      run_upgrade "$@"
  ) 9> $LOCK_FILE
}



case "$1" in
  --switch-to-version)
   case "$2" in
     "") error '--switch-to-version requires parameter' ;;
     *) switch_to_version $2 ; exit ;;
   esac ;;
  --version) show_version ; exit ;;
  *) upgrade "$@" ; exit ;;
esac
