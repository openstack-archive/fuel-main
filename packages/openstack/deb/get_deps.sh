#!/bin/bash

# Get runtime dependencies for rebuilt OpenStack components
# (yumdownloader replacement for Ubuntu)
# Script is meant to be executed from within Ubuntu chroot
# Input: /$COMPONENT.pkg.list - with list of rebuilt packages
# Output: downloaded runtime dependencies in /repo/download

mkdir -p /repo/download/
xargs -d '\n' -- apt-get -y install --download-only -o Dir::Cache="/repo" -o Dir::Cache::archives="/repo/download" < /*.pkg.list

# Dowmloaded dependencies may contain the same pre-built packages from master repository,
# so let's remove them

for pkg in `cat *.pkg.list`; do EXPR=".*"$pkg"_[^-]+-[^-]+.*" ; find /repo/download -regex $EXPR -delete ; done

rm -f *.pkg.list