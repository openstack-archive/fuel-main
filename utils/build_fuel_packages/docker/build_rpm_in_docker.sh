#!/bin/bash

# This script runs inside docker env, please check build_deb.sh file
# for required input data

set -ex

# update env
sudo yum update -y
# check BuildRequires
sudo yum-builddep -y /opt/sandbox/*.spec
# build package
rpmbuild --nodeps --define "_topdir /opt/sandbox" \
  --define "release $(awk -F'=' '/RELEASE/ {print $2}' /opt/sandbox/SOURCES/version)" -ba /opt/sandbox/*.spec
