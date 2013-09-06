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

GlobalPaths() {
  ISO_DIR="${ISO_DIR:=/var/www/fuelweb-iso}"
  export ISO_NAME="${JOB_NAME%.*}.iso"
  export ISO_PATH="${ISO_DIR}/${ISO_NAME}"
  TASK_NAME="${JOB_NAME##*.}"
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

  USE_MIRROR="${USE_MIRROR:=srt}"
  export USE_MIRROR

  # clean previous garbage
  make deep_clean
  ec=$?

  if [ $ec -gt 0 ]; then
    echo "Error! Deep clean failed!"
    exit $ec
  fi

  # create ISO file
  make iso
  ec=$?

  if [ $ec -gt 0 ]; then
    echo "Error! Make ISO!"
    exit $ec
  fi

  ISO=`ls ${WORKSPACE}/build/iso/*.iso | head -n 1`

  # check that ISO file exists
  if [ ! -f "${ISO}" ]; then
    echo "Error! ISO file not found!"
    exit 1
  fi

  # create shared iso dir if not present
  mkdir -p "${ISO_DIR}"

  # copy ISO file to storage dir
  cp "${ISO}" "${ISO_PATH}"
  ec=$?

  if [ $ec -gt 0 ]; then
    echo "Error! Copy ISO from ${ISO} to ${ISO_PATH} failed!"
    exit $ec
  fi
  echo "Finished building ISO: ${ISO_PATH}"
  exit 0
}

RunTest() {
  # Run test selected by task name

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

  # remove created environment
  dos.py destroy "${ENV_NAME}"

  exit 0
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
GlobalPaths
RouteTasks
