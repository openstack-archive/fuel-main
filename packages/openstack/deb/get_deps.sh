#!/bin/bash

# Get runtime dependencies for rebuilt OpenStack components
# (yumdownloader replacement for Ubuntu)
# Script is meant to be executed from within Ubuntu chroot
# Input: /$COMPONENT.pkg.list - with list of rebuilt packages
# Output: downloaded runtime dependencies in /repo/download

apt-get update
mkdir -p /repo/download/
cat /*.pkg.list | while read pkg; do apt-get --print-uris --yes install $pkg | grep ^\' | cut -d\' -f2 >/downloads_$pkg.list; done
cat /downloads_*.list | sort | uniq > /repo/download/download_urls.list
(cat /repo/download/download_urls.list | xargs -n1 -P4 wget -nv -P /repo/download/) || exit 1
mv /var/cache/apt/archives/*deb /repo/download/

# Dowmloaded dependencies may contain the same pre-built packages from master repository,
# so let's remove them

for pkg in `cat *.pkg.list`; do EXPR=".*"$pkg"_[^-]+-[^-]+.*" ; find /repo/download -regex $EXPR -delete ; done
rm /downloads_*.list /*.pkg.list