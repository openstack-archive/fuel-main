#!/bin/sh
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# functions

ShowHelp() {
cat << EOF
System Tests Script

It can perform several actions depending on Jenkins JOB_NAME it's ran from
or it can take names from exported environment variables or command line options
if you do need to override them.

-w (dir)    - Path to workspace where fuelweb git repository was checked out.
              Uses Jenkins' WORKSPACE if not set
-j (name)   - Name of this job. Determines ISO name, Task name and used by tests.
              Uses Jenkins' JOB_NAME if not set
-i (file)   - Full path to ISO file to build or use for tests.
              Made from iso dir and name if not set.
-t (name)   - Name of task this script should perform. Should be one of defined ones.
              Taken from Jenkins' job's suffix if not set.
-T (class)  - Overrides what tests should be ran insted of using task system.
              Set if you want to run custom test.
-a (str)    - Allows you to path NOSE_ATTR to the test job if you want
              to use some parameters.
-A (str)    - Allows you to path  NOSE_EVAL_ATTR if you want to enter attributes
              as python expressions.
-m (name)   - Use this mirror to build ISO from.
              Uses 'srt' if not set.
-r (yes/no) - Should built ISO file be places with build number tag and
              symlinked to the last build or just copied over the last file.
-b (num)    - Allows you to override Jenkins' build number if you need to.
-d          - Dry run mode. Only show what would be done and do nothing.
              Useful for debugging.
-h          - Show this help page

Most variables uses guesing from Jenkins' job name but can be overriden
by exported variable before script is run or by one of command line options.

You can override following variables using export VARNAME="value" before running this script
WORKSPACE  - path to directory where Fuelweb repository was checked out by Jenkins or manually
JOB_NAME   - name of Jenkins job that determines which task should be done and ISO file name.

If task name is "iso" it will make iso file
Other defined names will run Nose tests using previously built ISO file.

ISO file name is taken from job name prefix
Task name is taken from job name suffix
Separator is one dot '.'

For example if JOB_NAME is:
mytest.somestring.iso
ISO name: mytest.iso
Task name: iso
If ran with such JOB_NAME iso file with name mytest.iso will be created

If JOB_NAME is:
mytest.somestring.node
ISO name: mytest.iso
Task name: node
If script was run with this JOB_NAME node tests will be using ISO file mytest.iso.

First you should run mytest.somestring.iso job to create mytest.iso.
Then you can ran mytest.somestring.node job to start tests using mytest.iso and other tests too.
EOF
}

GlobalVariables() {
  # where built iso's should be placed
  # use hardcoded default if not set before by export
  ISO_DIR="${ISO_DIR:=/var/www/fuelweb-iso}"

  # name of iso file
  # taken from jenkins job prefix
  # if not set before by variable export
  if [ -z "${ISO_NAME}" ]; then
    ISO_NAME="${JOB_NAME%.*}.iso"
  fi

  # full path where iso file should be placed
  # make from iso name and path to iso shared directory
  # if was not overriden by options or export
  if [ -z "${ISO_PATH}" ]; then
    ISO_PATH="${ISO_DIR}/${ISO_NAME}"
  fi  
  
  # what task should be ran
  # it's taken from jenkins job name suffix if not set by options
  if [ -z "${TASK_NAME}" ]; then
    TASK_NAME="${JOB_NAME##*.}"
  fi

  # do we want to keep iso's for each build or just copy over single file
  ROTATE_ISO="${ROTATE_ISO:=yes}"

  # choose mirror to build iso from. Default is 'srt' for Saratov's mirror
  # you can change mirror by exporting USE_MIRROR variable before running this script
  USE_MIRROR="${USE_MIRROR:=srt}"

  # only show what commands would be executed but do nothing
  # this feature is usefull if you want to debug this script's behaviour
  DRY_RUN="${DRY_RUN:=no}"
}

GetoptsVariables() {
  while getopts ":w:j:i:t:T:a:A:m:r:b:dh" opt; do
    case $opt in
      w)
        WORKSPACE="${OPTARG}"
        ;;
      j)
        JOB_NAME="${OPTARG}"
        ;;
      i)
        ISO_PATH="${OPTARG}"
        ;;
      t)
        TASK_NAME="${OPTARG}"
        ;;
      T)
        TEST_NAME="${OPTARG}"
        ;;
      a)
        NOSE_ATTR="${OPTARG}"
        ;;
      A)
        NOSE_EVAL_ATTR="${OPTARG}"
        ;;
      m)
        USE_MIRROR="${OPTARG}"
        ;;
      r)
        ROTATE_ISO="${OPTARG}"
        ;;
      b)
        BUILD_NUMBER="${OPTARG}"
        ;;
      d)
        DRY_RUN="yes"
        ;;
      h)
        ShowHelp
        exit 0
        ;;
      \?)
        echo "Invalid option: -$OPTARG"
        ShowHelp
        exit 1
        ;;
      :)
        echo "Option -$OPTARG requires an argument."
        ShowHelp
        exit 1
        ;;
    esac
  done
}

CheckVariables() {

  if [ -z "${JOB_NAME}" ]; then
    echo "Error! JOB_NAME is not set!"
    exit 1
  fi

  if [ -z "${ISO_PATH}" ]; then
    echo "Error! ISO_PATH is not set!"
    exit 1
  fi
  
  if [ -z "${TASK_NAME}" ]; then
    echo "Error! TASK_NAME is not set!"
    exit 1
  fi

  if [ -z "${WORKSPACE}" ]; then
    echo "Error! WORKSPACE is not set!"
    exit 1
  fi
}

MakeISO() {
  # Create iso file to be used in tests

  # clean previous garbage
  if [ "${DRY_RUN}" = "yes" ]; then
    echo make deep_clean
  else
    make deep_clean
  fi
  ec="${?}"

  if [ "${ec}" -gt "0" ]; then
    echo "Error! Deep clean failed!"
    exit "${ec}"
  fi

  # create ISO file
  export USE_MIRROR
  if [ "${DRY_RUN}" = "yes" ]; then
    echo make iso
  else
    make iso
  fi
  ec=$?

  if [ "${ec}" -gt "0" ]; then
    echo "Error making ISO!"
    exit "${ec}"
  fi

  if [ "${DRY_RUN}" = "yes" ]; then
    ISO="${WORKSPACE}/build/iso/fuel.iso"
  else
    ISO="`ls ${WORKSPACE}/build/iso/*.iso | head -n 1`"
    # check that ISO file exists
    if [ ! -f "${ISO}" ]; then
      echo "Error! ISO file not found!"
      exit 1
    fi
  fi

  # copy ISO file to storage dir
  # if rotation is enabled and build number is aviable
  # save iso to tagged file and symlink to the last build
  # if rotation is not enabled just copy iso to iso_dir

  if [ "${ROTATE_ISO}" = "yes" -a "${BUILD_NUMBER}" != "" ]; then
    # copy iso file to shared dir with revision tagged name
    NEW_BUILD_ISO_PATH="${ISO_PATH#.iso}_${BUILD_NUMBER}.iso"
    if [ "${DRY_RUN}" = "yes" ]; then
      echo cp "${ISO}" "${NEW_BUILD_ISO_PATH}"
    else
      cp "${ISO}" "${NEW_BUILD_ISO_PATH}"
    fi
    ec=$?

    if [ "${ec}" -gt "0" ]; then
      echo "Error! Copy ${ISO} to ${NEW_BUILD_ISO_PATH} failed!"
      exit "${ec}"
    fi

    # create symlink to the last built ISO file
    if [ "${DRY_RUN}" = "yes" ]; then
      echo ln -sf "${NEW_BUILD_ISO_PATH}" "${ISO_PATH}"
    else
      ln -sf "${NEW_BUILD_ISO_PATH}" "${ISO_PATH}"
    fi
    ec=$?

    if [ "${ec}" -gt "0" ]; then
      echo "Error! Create symlink from ${NEW_BUILD_ISO_PATH} to ${ISO_PATH} failed!"
      exit "${ec}"
    fi
  else
    # just copy file to shared dir
    if [ "${DRY_RUN}" = "yes" ]; then
      echo cp "${ISO}" "${ISO_PATH}"
    else
      cp "${ISO}" "${ISO_PATH}"
    fi
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

CdWorkSpace() {
  # chdir into workspace or fail if could not
  if [ "${DRY_RUN}" != "yes" ]; then
    cd "${WORKSPACE}"
    ec=$?

    if [ "${ec}" -gt "0" ]; then
      echo "Error! Cannot cd to WORKSPACE!"
      exit "${ec}"
    fi
  fi
}

RunCustomTest() {
  # if TEST_NAME is set we override task selector and run this test instead
  if [ -n "${TEST_NAME}" ]; then
    RunTest "${TEST_NAME}"
    exit 0
  fi
}

RunTest() {
  # Run test selected by task name

  # check if iso file exists
  if [ ! -f "${ISO_PATH}" -a "${DRY_RUN}" != "yes" ]; then
    echo "Error! File ${ISO_PATH} not found!"
    exit 1
  fi

  # run python virtualenv
  if [ "${DRY_RUN}" = "yes" ]; then
    echo . ~/venv-nailgun-tests/bin/activate
  else
    . ~/venv-nailgun-tests/bin/activate
  fi

  export ENV_NAME="${JOB_NAME}_system_test"
  export LOGS_DIR="${WORKSPACE}/logs"
  export ISO_PATH

  # remove previous garbage
  if [ "${DRY_RUN}" = "yes" ]; then
    echo dos.py erase "${ENV_NAME}"
  else
    dos.py erase "${ENV_NAME}"
  fi

  # gather additional option for this nose test run
  OPTS=""
  if [ -n "${NOSE_ATTR}" ]; then
    OPTS="${OPTS} -a ${NOSE_ATTR}"
  fi
  if [ -n "${NOSE_EVAL_ATTR}" ]; then
    OPTS="${OPTS} -A ${NOSE_EVAL_ATTR}"
  fi

  # run python test set to create environments, deploy and test product
  if [ "${DRY_RUN}" = "yes" ]; then
    echo nosetests -w "fuelweb_test" -s -l DEBUG ${OPTS} --with-xunit "${1}"
  else
    nosetests -w "fuelweb_test" -s -l DEBUG ${OPTS} --with-xunit "${1}"
  fi
  ec=$?

  # remove previous garbage
  if [ "${DRY_RUN}" = "yes" ]; then
    echo dos.py destroy "${ENV_NAME}"
  else
    dos.py destroy "${ENV_NAME}"
  fi

  exit "${ec}"
}

RouteTasks() {
  # this selector defines task names that are recognised by this script
  # and runs corresponding jobs for them
  # running any jobs should exit this script

  case "${TASK_NAME}" in
  test)
    RunTest
    ;;  
  iso)
    MakeISO
    ;;
  *)
    echo "Unknown task: ${TASK_NAME}!"
    exit 1
    ;;
  esac
  exit 0
}

# MAIN

# first we want to get variable from command line options
GetoptsVariables ${@}

# then we define global variables and there defaults when needed
GlobalVariables

# check do we have all critical variables set
CheckVariables

# first we chdir into our working directory unless we dry run
CdWorkSpace

# run custom test if TEST_NAME is set
RunCustomTest

# finally we can choose what to do according to TASK_NAME
RouteTasks
