#!/bin/sh
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# functions

GlobalPaths() {
  # global paths

  ISO_DIR="${JENKINS_HOME}/iso"
  ISO_NAME="${JOB_NAME%.*}.iso"
  ISO_PATH="${ISO_DIR}/${ISO_NAME}"
  TASK_NAME="${JOB_NAME##*.}"
}

GetoptsVariables() {
  while getopts ":j:n:w:h" opt; do
    case $opt in
      j)
        JENKINS_HOME="${OPTARG}"
        ;;
      n)
        JOB_NAME="${OPTARG}"
        ;;
      w)
        WORKSPACE="${OPTARG}"
        ;;
      h)
        ShowHelp
        exit 0
        ;;
      \?)
        echo "Invalid option: -$OPTARG" >&2
        ShowHelp
        exit 1
        ;;
      :)
        echo "Option -$OPTARG requires an argument." >&2
        ShowHelp
        exit 1
        ;;
    esac
  done
}

ShowHelp() {
cat <<EOF
System Tests Script

It can perform several actions depending on Jenkins JOB_NAME it is ran from
or it can take variables from arguments if you do need to override these values.

If task name is "iso" it will make iso file
Other defined test names will ran nose tests with made iso file

Iso file name is taken from job name prefix
Task name is taken from job name suffix
Separator is one dot '.'

For example if task name is:
mytest.somestring.iso
ISO name: mytest.iso
Task name: iso
If ran with such JOB_NAME iso file with name mytest.iso will be created
If task name is:
mytest.somestring.node
ISO name: mytest.iso
Task name: node
If ran with such JOB_NAME node tests will be ran using iso file mytest.iso

First you should ran mytest.somestring.iso to create mytest.iso
Then you can ran mytest.somestring.node to run tests using mytest.iso and other tests too.

You also can override variables with these options:

  -j (path) - JENKINS_HOME
  -n (name) - JOB_NAME
  -w (path) - WORKSPACE
  -h        - Show this help

EOF
}

CheckVariables() {
  # variable checks

  if [ -z "${JENKINS_HOME}" ]; then
    echo "Error! JENKINS_HOME is not set!"
    exit 1
  fi

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
  cp "${ISO}" "${ISO_DIR}/${ISO_NAME}"
  ec=$?

  if [ $ec -gt 0 ]; then
    echo "Error! Copy ISO from ${ISO} to ${ISO_PATH}/${ISO_NAME} failed!"
    exit $ec
  fi

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
  export ISO_NAME
  export ISO_PATH

  # remove previous garbage
  dos.py erase "${ENV_NAME}"

  # run python test set to create environments, deploy and test product
  nosetests -w "${WORKSPACE}" -s -l DEBUG --with-xunit "${1}"

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
GetoptsVariables $@
CheckVariables
GlobalPaths
RouteTasks
