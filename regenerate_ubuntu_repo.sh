#!/bin/bash

#    Copyright 2014 Mirantis, Inc.
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

#    This script will rebuild local ubuntu mirror.
#    Based on the method described here:
#    http://troubleshootingrange.blogspot.com/2012/09/hosting-simple-apt-repository-on-centos.html

#    Example:
#    regenerate_ubuntu_repo /path/to/ubuntu/repo precise

REPO_PATH=$1
REPONAME=$2

BINDIR=${REPO_PATH}/dists/${REPONAME}/main
package_deb=${BINDIR}/binary-amd64/Packages
release_header=`head -8 ${REPO_PATH}/dists/${REPONAME}/Release`

cd ${REPO_PATH}
echo "Regenerating Ubuntu local mirror..."

# Scan *.deb packages
dpkg-scanpackages -a amd64 pool/main  > $package_deb 2>/dev/null
gzip -9c $package_deb > ${package_deb}.gz

# Generate release file
cd ${REPO_PATH}/dists/${REPONAME}
echo "$release_header" > Release

# Generate hashes
c1=(MD5Sum: SHA1: SHA256: SHA512:)
c2=(md5 sha1 sha256 sha512)

i=0
while [ $i -lt ${#c1[*]} ]; do
    echo ${c1[i]} >> Release
        for hashme in `find main -type f \( -name "Package*" -o -name "Release*" \)`; do
        chash=`openssl dgst -${c2[$i]} ${hashme}|cut -d" " -f 2`
        size=`stat -c %s ${hashme}`
        echo " ${chash} ${size} ${hashme}" >> Release
    done
    i=$(( $i + 1));
done
