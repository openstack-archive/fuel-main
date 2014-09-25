#!/bin/bash

NEWER=$1
OLDER=$2
DIFF=$3

# we need to check if OLDER dir exists
# if not, nothing to compare return exit 1
test -d ${OLDER} || { echo "${OLDER} path doesn't exist, nothing to compare"; exit 1; }

test -d ${DIFF} || mkdir -p ${DIFF}

function copy_by_checksum (){
  # compare files by checksum
  CHECKSUM1=$(md5sum -- $1 | awk '{print $1}')
  CHECKSUM2=$(md5sum -- $2 | awk '{print $1}')

  # if checksum is different then copy
  [ $CHECKSUM1 = $CHECKSUM2 ] || cp -av $1 $3
}

export -f copy_by_checksum

# if file doesn't exists in old, then copy it to diff
# else compare by checksum
find ${NEWER} -type f -printf "%f\n" | xargs -i bash -c "test -f ${OLDER}/{} \
  &&  copy_by_checksum ${NEWER}/{} ${OLDER}/{} ${DIFF} \
  || cp -av ${NEWER}/{} ${DIFF}/{}"
