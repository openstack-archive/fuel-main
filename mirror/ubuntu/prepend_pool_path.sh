#!/bin/bash
#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

set -ex

PATH_TO_FIX=$1
PREPEND_POOL_PATH=$2

RELEASE_FILE=${PATH_TO_FIX}/Release
[ ! -f "${RELEASE_FILE}" ] && exit 1
RELEASE_HEADER="$(sed -r '/^\s*[0-9a-fA-F]{32,}|MD5|SHA/ d' ${RELEASE_FILE})"
PACKAGES_FILES=$(find ${PATH_TO_FIX} -name Packages)

# prepend paths
for package_file in $PACKAGES_FILES ; do
  rm -f ${package_file}.*
  sed -i "s|^Filename: pool/|Filename: ${PREPEND_POOL_PATH}pool/|g" ${package_file}
  gzip -9c ${package_file} > ${package_file}.gz
done

# Regenerate Release file
FILES_LIST=""
dirs_to_look_at=$(find ${PATH_TO_FIX} -maxdepth 1 -mindepth 1 -type d -not -name 'pool')
for _dir in ${dirs_to_look_at} ; do
  FILES_LIST="${FILES_LIST} $(find ${_dir} -type f)"
done

echo "${RELEASE_HEADER}" > ${RELEASE_FILE}

# Regenerate hashes
hash_headers=(MD5Sum: SHA1: SHA256: SHA512:)
hash_cmds=(md5 sha1 sha256 sha512)

_index=0
while [ $_index -lt ${#hash_headers[*]} ]; do
  echo ${hash_headers[_index]} >> ${RELEASE_FILE}

  for file in ${FILES_LIST} ; do
      file_hash=$(openssl dgst -${hash_cmds[_index]} ${file} | cut -d" " -f 2)
      file_size=$(stat -c %s ${file})
      file_name=$(echo $file | sed "s|^${PATH_TO_FIX}/||")
      echo " ${file_hash} ${file_size} ${file_name}" >> ${RELEASE_FILE}
  done
  _index=$(( _index + 1))
done
