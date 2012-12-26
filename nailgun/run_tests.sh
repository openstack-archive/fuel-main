#!/bin/bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run tests"
  echo ""
  echo "  -p, --pep8               Just run PEP8 and HACKING compliance check"
  echo "  -f, --fail-first         Nosetests will stop on first error"
  echo "  -j, --jslint             Just run JSLint"
  echo "  -u, --ui-tests           Just run UI tests"
  echo "  -x, --xunit              Generate reports (useful in Jenkins environment)"
  echo "  -P, --no-pep8            Don't run static code checks"
  echo "  -J, --no-jslint          Don't run JSLint"
  echo "  -U, --no-ui-tests        Don't run UI tests"
  echo "  -c, --clean              Only clean *.log, *.json, *.pyc, *.pid files, doesn't run tests"
  echo "  -h, --help               Print this usage message"
  echo ""
  echo "By default it runs tests and pep8 check."
  exit
}

function process_option {
  case "$1" in
    -h|--help) usage;;
    -p|--pep8) just_pep8=1;;
    -f|--fail-first) fail_first=1;;
    -j|--jslint) just_jslint=1;;
    -u|--ui-tests) just_ui_tests=1;;
    -P|--no-pep8) no_pep8=1;;
    -J|--no-jslint) no_jslint=1;;
    -U|--no-ui-tests) no_ui_tests=1;;
    -x|--xunit) xunit=1;;
    -c|--clean) clean=1;;
    ui_tests*) ui_test_files="$ui_test_files $1";;
    -*) noseopts="$noseopts $1";;
    *) noseargs="$noseargs $1"
  esac
}

just_pep8=0
no_pep8=0
fail_first=0
just_jslint=0
no_jslint=0
just_ui_tests=0
no_ui_tests=0
xunit=0
clean=0
ui_test_files=
noseargs=
noseopts=

for arg in "$@"; do
  process_option $arg
done

if [ -n "$ui_test_files" ]; then
    just_ui_tests=1
fi

function clean {
  echo "cleaning *.pyc, *.json, *.log, *.pid files"
  find . -type f -name "*.pyc" -delete
  rm -f *.json
  rm -f *.log
  rm -f *.pid
}

if [ $clean -eq 1 ]; then
  clean
  exit 0
fi

# If enabled, tell nose to create xunit report
if [ $xunit -eq 1 ]; then
    noseopts=${noseopts}" --with-xunit"
fi

if [ $fail_first -eq 1 ]; then
    noseopts=${noseopts}" --stop"
fi

function run_pep8 {
  pep8 --show-source --show-pep8 --count . || return 1
  echo "PEP8 check passed successfully."
}

if [ $just_pep8 -eq 1 ]; then
    run_pep8 || exit 1
    exit
fi

function run_jslint {
    which jslint > /dev/null
    if [ $? -ne 0 ]; then
        echo "JSLint is not installed; install by running:"
        echo "sudo apt-get install npm"
        echo "sudo npm install -g jslint"
        return 1
    fi
    jsfiles=$(find static/js -type f | grep -v ^static/js/libs/ | grep \\.js$)
    jslint_predef=(requirejs require define app Backbone $ _ alert confirm)
    jslint_options="$(echo ${jslint_predef[@]} | sed 's/^\| / --predef=/g') --browser=true --nomen=true --eqeq=true --vars=true --white=true --es5=false"
    jslint $jslint_options $jsfiles || return 1
}

if [ $just_jslint -eq 1 ]; then
    run_jslint || exit 1
    exit
fi

function run_ui_tests {
    which casperjs > /dev/null
    if [ $? -ne 0 ]; then
        echo "CasperJS is not installed; install by running:"
        echo "sudo apt-get install phantomjs"
        echo "cd ~"
        echo "git clone git://github.com/n1k0/casperjs.git"
        echo "cd casperjs"
        echo "git checkout tags/1.0.0-RC4"
        echo "sudo ln -sf \`pwd\`/bin/casperjs /usr/local/bin/casperjs"
        return 1
    fi
    ui_tests_dir=ui_tests
    if [ -z "$ui_test_files" ]; then
        ui_test_files=$ui_tests_dir/test_*.js
    fi
    result=0
    ./manage.py run --port=5544 --fake-tasks --fake-tasks-tick-count=6 --fake-tasks-tick-interval=1 > /dev/null 2>&1 &
    for test_file in $ui_test_files; do
        rm -f nailgun.sqlite
        ./manage.py syncdb > /dev/null
        ./manage.py loaddata $ui_tests_dir/fixture.json > /dev/null
        casperjs test --includes=$ui_tests_dir/helpers.js --fail-fast $test_file
        result=$(($result + $?))
    done
    kill %1
    return $result
}

if [ $just_ui_tests -eq 1 ]; then
    run_ui_tests || exit 1
    exit
fi

function run_tests {
  clean
  [ -z "$noseargs" ] && test_args=. || test_args="$noseargs"
  nosetests $noseopts $test_args
}

errors=''

run_tests || errors+=' unittests'

if [ -z "$noseargs" ]; then
  if [ $no_pep8 -eq 0 ]; then
    run_pep8 || errors+=' pep8'
  fi
  if [ $no_jslint -eq 0 ]; then
    run_jslint || errors+=' jslint'
  fi
  if [ $no_ui_tests -eq 0 ]; then
    run_ui_tests || errors+=' ui-tests'
  fi
fi

if [ -n "$errors" ]; then
  echo Failed tests: $errors
  exit 1
fi
