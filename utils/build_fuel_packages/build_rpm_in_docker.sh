#!/bin/bash

# This script runs inside docker env, please check build_deb.sh file
# for required input data

set -ex

# check BuildRequires
sudo yum-builddep -y /opt/sandbox/*.spec
# build package
rpmbuild --nodeps -vv --define "_topdir /opt/sandbox" -ba /opt/sandbox/*.spec
