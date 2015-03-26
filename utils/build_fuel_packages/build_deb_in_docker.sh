#!/bin/bash

# This script runs inside docker env, please check build_deb.sh file
# for required input data

set -ex

mkdir -p /tmp/package

# since we have specs in repo we can prepare for build faster
# just unpack prepared sources
tar -xzf /opt/sandbox/SOURCES/*gz -C /tmp/package

dpkg-checkbuilddeps /tmp/package/debian/control 2>&1 | \
  sed 's/^dpkg-checkbuilddeps: Unmet build dependencies: //g' | \
  sed 's/([^()]*)//g;s/|//g' | tee /tmp/package.installdeps

/bin/sh -c "cat /tmp/package.installdeps | xargs --no-run-if-empty sudo apt-get -y install"
/bin/sh -c "cd /tmp/package ; DEB_BUILD_OPTIONS=nocheck debuild -us -uc -b -d"
cp -v /tmp/*.deb /opt/sandbox/DEB
