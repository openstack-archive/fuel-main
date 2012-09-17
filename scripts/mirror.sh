#!/bin/bash

# Script should be run from product root directory
[ -z $1 ] && echo "Use: mirror.sh mirror_directory" && exit 1 \
|| MIRROR_DIR_EGGS=$1/eggs && MIRROR_DIR_GEMS=$1/gems

[ -f ./requirements-eggs.txt ] && [ -f ./requirements-gems.txt ] || echo "Could find requirements-eggs.txt/requirement-gems.txt file(s)\nTry to run this script from project root directory" && exit 1

# creating/updating repo for eggs
[ -d $MIRROR_DIR_EGGS ] || mkdir $MIRROR_DIR_EGGS
awk -v mirror=$MIRROR_DIR_EGGS '{system ("[ `find " mirror " -name " $1 "-" $2 "* ` ] || pip install -d " mirror " " $1 "=="$2 )}' ./requirements-eggs.txt

# creating/updating repo for gems
[ -d $MIRROR_DIR_GEMS ] || mkdir $MIRROR_DIR_GEMS
awk -v mirror=$MIRROR_DIR_GEMS '{system ("[ `find " mirror " -name " $1 "-" $2 "*` ] || ( cd "mirror" && gem fetch "$1" -v "$2")")}' ./requirements-gems.txt

echo "Mirrors are updated"
exit 0