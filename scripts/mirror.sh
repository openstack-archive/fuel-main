#!/bin/bash

# Script should be run from directory that contains requirements files
[ -z $1 -a -z $2 ] && echo "Use: mirror.sh remote_mirror_path local_mirror_directory" && exit 1 

MIRROR_SERVER=$1
HOSTNAME=`hostname`
LOCAL_MIRROR=$2

# checking is server trying to sync from itself or not
if [[ $MIRROR_SERVER =~ $HOSTNAME.*:(.*) ]]
then

    LOCAL_PATH=${BASH_REMATCH[1]}
    MIRROR_DIR_EGGS=$LOCAL_PATH/eggs
    MIRROR_DIR_GEMS=$LOCAL_PATH/gems

    [ -f ./requirements-eggs.txt -a -f ./requirements-gems.txt ] || ( echo "Couldn't find requirements-eggs.txt/requirement-gems.txt file(s)\nTry to run this script from project root directory" && exit 1 )

    # creating/updating repo for eggs
    [ -d $MIRROR_DIR_EGGS ] || mkdir -p $MIRROR_DIR_EGGS
    awk -v mirror=$MIRROR_DIR_EGGS '{system ("[ `find " mirror " -name " $1 "-" $2 "* ` ] || pip install -d " mirror " " $1 "=="$2 )}' ./requirements-eggs.txt

    # creating/updating repo for gems
    [ -d $MIRROR_DIR_GEMS ] || mkdir -p $MIRROR_DIR_GEMS
    awk -v mirror=$MIRROR_DIR_GEMS '{system ("[ `find " mirror " -name " $1 "-" $2 "*` ] || ( cd "mirror" && gem fetch "$1" -v "$2")")}' ./requirements-gems.txt

    ln -s ${BASH_REMATCH[1]} ./mirror
    echo "Local golden mirror is updated from the internet."
    echo "Symlink to ${BASH_REMATCH[1]} created at the build dir"

else

    # rsyncing from the golden mirror and
    # assuming that current user have access to the root user of golden mirror using public keys
    rsync -e 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' --size-only -r root@$MIRROR_SERVER/* $LOCAL_MIRROR || (echo "Couldn't Rsync with Golden Mirror" && exit 1)
    echo "Local mirror updated from the golden mirror"

fi
