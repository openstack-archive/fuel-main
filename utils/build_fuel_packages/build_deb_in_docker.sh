#!/bin/bash

set -x

for pkgs in $(ls /opt/sandbox/SPECS/); do
  mkdir /tmp/${pkgs}
  cp -rv /opt/sandbox/SOURCES/${pkgs}/* /tmp/${pkgs}/
  cp -rv /opt/sandbox/SPECS/${pkgs}/* /tmp/${pkgs}/
  dpkg-checkbuilddeps /opt/sandbox/SPECS/${pkgs}/debian/control 2>&1 | sed 's/^dpkg-checkbuilddeps: Unmet build dependencies: //g' | sed 's/([^()]*)//g;s/|//g' | tee /tmp/${pkgs}.installdeps
  /bin/sh -c "cat /tmp/${pkgs}.installdeps | xargs apt-get -y install"
  /bin/sh -c "cd /tmp/${pkgs} ; DEB_BUILD_OPTIONS=nocheck debuild -us -uc -b -d"
  cp -v /tmp/*${pkgs}*.deb /opt/sandbox/DEB
done
