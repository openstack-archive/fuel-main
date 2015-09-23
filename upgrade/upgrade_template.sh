#!/bin/bash

SCRIPT_PATH=$(dirname $(readlink -e $0))
UPGRADE_PATH=$SCRIPT_PATH/upgrade
VIRTUALENV_PATH=$UPGRADE_PATH/.fuel-upgrade-venv
UPGRADERS=${UPGRADERS:-{{UPGRADERS}}}
LOCK_FILE=/var/lock/fuel_upgarde.lock


function error {
  local message="$1"
  local code="${2:-1}"

  echo "${message}"

  exit "${code}"
}


function prepare_virtualenv {

  if ! which virtualenv >/dev/null; then
    yum -y install python-virtualenv || error "Failed to install python-virtualenv"
  fi

  rm -rf $VIRTUALENV_PATH
  virtualenv $VIRTUALENV_PATH
  $VIRTUALENV_PATH/bin/pip install fuel_upgrade --no-index --find-links file://$UPGRADE_PATH/deps || error "Failed to install fuel_upgrade script"
}


function run_upgrade {
  # prepare virtualenv for fuel_upgrade script
  prepare_virtualenv

  local args=()
  local kwargs=("--src=$UPGRADE_PATH")

  while [ -n "$1" ]; do
    if [ $1 == \-\-password ]; then
      kwargs=("${kwargs[@]}" "$1=$2"); shift
    elif [[ $1 == \-* ]]; then
      kwargs=("${kwargs[@]}" "$1")
    else
      args=("${args[@]}" "$1")
    fi
    shift
  done

  [ -z "${args[0]}" ] && args=("${UPGRADERS[@]}")

  # run fuel_upgrade script
  $VIRTUALENV_PATH/bin/python "$VIRTUALENV_PATH/bin/fuel-upgrade" "${kwargs[@]}" ${args[@]} || \
    error "Upgrade failed" $?
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
