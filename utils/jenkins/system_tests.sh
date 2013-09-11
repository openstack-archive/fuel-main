#!/bin/sh
# System Tests Script
#
# It can perform several actions depending on Jenkins JOB_NAME it is ran from
# or it can take variables from arguments if you do need to override these values.
#
# If task name is "iso" it will make iso file
# Other defined test names will ran nose tests with made iso file
#
# Iso file name is taken from job name prefix
# Task name is taken from job name suffix
# Separator is one dot '.'
#
# For example if task name is:
# mytest.somestring.iso
# ISO name: mytest.iso
# Task name: iso
# If ran with such JOB_NAME iso file with name mytest.iso will be created
# If task name is:
# mytest.somestring.node
# ISO name: mytest.iso
# Task name: node
# If ran with such JOB_NAME node tests will be ran using iso file mytest.iso
#
# First you should ran mytest.somestring.iso to create mytest.iso
# Then you can ran mytest.somestring.node to run tests using mytest.iso and other tests too.

PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# functions

GlobalVars() {
  # where built iso's should be placed
  ISO_DIR="${ISO_DIR:=/var/www/fuelweb-iso}"
  # name of iso file
  export ISO_NAME="${JOB_NAME%.*}.iso"
  # full path where iso file should be placed
  export ISO_PATH="${ISO_DIR}/${ISO_NAME}"
  # what task should be ran
  TASK_NAME="${JOB_NAME##*.}"
  # do we want to keep iso's for each build or just copy over single file
  ROTATE_ISO="${ROTATE_ISO:=yes}"
  # what mirror should be used during iso building process
  export USE_MIRROR="${USE_MIRROR:=srt}"
}

CheckVariables() {
  if [ -z "${JOB_NAME}" ]; then
    echo "Error! JOB_NAME is not set!"
    exit 1
  fi

  if [ -z "${WORKSPACE}" ]; then
    echo "Error! WORKSPACE is not set!"
    exit 1
  fi
}

MakeISO() {
  # Create iso file to be used in tests

  # choose mirror to build iso from
  # default is 'srt' for Saratov mirror
  # if you export USE_MIRROR variable before
  # running this script
  # it's value will be used instead

  # clean previous garbage
  make deep_clean
  ec="${?}"

  if [ "${ec}" -gt "0" ]; then
    echo "Error! Deep clean failed!"
    exit "${ec}"
  fi

  # create ISO file
  make iso
  ec=$?

  if [ "${ec}" -gt "0" ]; then
    echo "Error! Make ISO!"
    exit "${ec}"
  fi

  ISO="`ls ${WORKSPACE}/build/iso/*.iso | head -n 1`"

  # check that ISO file exists
  if [ ! -f "${ISO}" ]; then
    echo "Error! ISO file not found!"
    exit 1
  fi

  # create shared iso dir if not present
  mkdir -p "${ISO_DIR}"

  # copy ISO file to storage dir
  # if rotation is enabled and build number is aviable
  # save iso to tagged file and symlink to the last build
  # if rotation is not enabled just copy iso to iso_dir

  if [ "${ROTATE_ISO}" = "yes" -a "${BUILD_NUMBER}" != "" ]; then
    # copy iso file to ISO_DIR with revision tagged name
    NEW_BUILD_ISO_PATH="${ISO_PATH#.iso}_${BUILD_NUMBER}.iso"
    cp "${ISO}" "${NEW_BUILD_ISO_PATH}"
    ec=$?

    if [ "${ec}" -gt "0" ]; then
      echo "Error! Copy ${ISO} to ${NEW_BUILD_ISO_PATH} failed!"
      exit "${ec}"
    fi

    # create symlink to the last built ISO file
    ln -sf "${NEW_BUILD_ISO_PATH}" "${ISO_PATH}"
    ec=$?

    if [ "${ec}" -gt "0" ]; then
      echo "Error! Create symlink from ${NEW_BUILD_ISO_PATH} to ${ISO_PATH} failed!"
      exit "${ec}"
    fi
  else
    cp "${ISO}" "${ISO_PATH}"
    ec=$?

    if [ "${ec}" -gt "0" ]; then
      echo "Error! Copy ${ISO} to ${ISO_PATH} failed!"
      exit "${ec}"
    fi
  fi

  if [ "${ec}" -gt "0" ]; then
    echo "Error! Copy ISO from ${ISO} to ${ISO_PATH} failed!"
    exit "${ec}"
  fi
  echo "Finished building ISO: ${ISO_PATH}"
  exit 0
}

RunTest() {
  # Run test selected by task name

  # first we chdir into our working directory
  cd "${WORKSPACE}"
  ec=$?

  if [ "${ec}" -gt "0" ]; then
    echo "Error! Cannot cd to WORKSPACE!"
    exit "${ec}"
  fi

  # check if iso file exists
  if [ ! -f "${ISO_PATH}" ]; then
    echo "Error! File ${ISO_PATH} not found!"
    exit 1
  fi

  # run python virtualenv
  . ~/venv-nailgun-tests/bin/activate

  export ENV_NAME="${JOB_NAME}_system_test"
  export LOGS_DIR="${WORKSPACE}/logs"

  # remove previous garbage
  dos.py erase "${ENV_NAME}"

  # run python test set to create environments, deploy and test product
  nosetests -w "fuelweb_test" -s -l DEBUG --with-xunit "${1}"
  ec=$?

  exit "${ec}"
}

RouteTasks() {
  # this selector defines task names that are recognised by this script
  # and runs corresponding jobs for them

  case "${TASK_NAME}" in
  admin_node)
    RunTest "fuelweb_test.integration.test_admin_node"
    ;;
  node)
    RunTest "fuelweb_test.integration.test_node:TestNode"
    ;;
  node_ha)
    RunTest "fuelweb_test.integration.test_node_ha"
    ;;
  node_ha2)
    RunTest "fuelweb_test.integration.test_node_ha2"
    ;;
  iso)
    MakeISO
    ;;
  *)
    echo "Unknown task: ${TASK_NAME}!"
    exit 1
    ;;
  esac
}

# MAIN
CheckVariables
GlobalVars
RouteTasks
