#!/bin/bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run tests"
  echo ""
  echo "  -p, --pep8               Just run PEP8 and HACKING compliance check"
  echo "  -j, --jslint             Just run JSLint"
  echo "  -x, --xunit              Generate reports (useful in Jenkins environment)"
  echo "  -P, --no-pep8            Don't run static code checks"
  echo "  -J, --no-jslint          Don't run JSLint"
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
    -j|--jslint) just_jslint=1;;
    -P|--no-pep8) no_pep8=1;;
    -J|--no-jslint) no_jslint=1;;
    -x|--xunit) xunit=1;;
    -c|--clean) clean=1;;
    -*) noseopts="$noseopts $1";;
    *) noseargs="$noseargs $1"
  esac
}

just_pep8=0
no_pep8=0
just_jslint=0
no_jslint=0
xunit=0
clean=0
noseargs=
noseopts=

for arg in "$@"; do
  process_option $arg
done

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
    noseopts="--with-xunit"
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
    jsfiles=$(find static/js -type f | grep -v ^static/js/libs/ | grep \\.js$)
    jslint_predef=(requirejs require define app Backbone $ _ alert confirm)
    jslint_options="$(echo ${jslint_predef[@]} | sed 's/^\| / --predef=/g') --browser=true --nomen=true --eqeq=true --sloppy=true --vars=true --white=true --es5=false"
    jslint $jslint_options $jsfiles || return 1
}

if [ $just_jslint -eq 1 ]; then
    run_jslint || exit 1
    exit
fi

function run_tests {
  clean
  [ -z "$noseargs" ] && test_args=. || test_args="$noseargs"
  nosetests $noseopts $test_args
}

run_tests || exit 1

if [ -z "$noseargs" ]; then
  if [ $no_pep8 -eq 0 ]; then
    run_pep8
  fi
  if [ $no_jslint -eq 0 ]; then
    run_jslint
  fi
fi
