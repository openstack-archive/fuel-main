#!/bin/bash -x

# 1. Update repo will be places in ${SROUCE}/local_mirror/centos_updates/os/x86_64/Packages
# 2. Please, replace "upstream/stable/5.1..upstream/master" with origin if you clone from github

BUILD_DIR=${PWD}/build
# original repo
CENTOS=${PWD}/local_mirror/centos/os/x86_64/Packages
# update repo
CENTOS_UPDATE=${PWD}/local_mirror/centos_updates/os/x86_64/Packages

PRODUCT_VERSION=5.1
LAST_VERSION=$(git show upstream/master:./config.mk | grep "PRODUCT_VERSION:=" | cut -d'=' -f2)

if [ "v${PRODUCT_VERSION}" == "v${LAST_VERSION}" ]; then
  echo "You have the same version."
  exit 0
fi

UPDATE_RPM=$(git diff upstream/stable/${PRODUCT_VERSION}..upstream/master requirements-rpm.txt | \
  grep ^+ | grep -v requirements-rpm.txt | cut -d'+' -f2)

if [ -z "${UPDATE_RPM}" ]; then
  echo "No packages for creating update repo."
  exit 0
fi

# clean previous version
rm -rf ${CENTOS_UPDATE}
# create repo folder
mkdir -p ${CENTOS_UPDATE}

yum -c ${BUILD_DIR}/mirror/centos/etc/yum.conf clean all

# put new version
sed -i "s/${PRODUCT_VERSION}/${LAST_VERSION}/" ${BUILD_DIR}/mirror/centos/etc/yum.repos.d/base.repo

# download only differences
yumdownloader --resolve --archlist=x86_64 \
  -c ${BUILD_DIR}/mirror/centos/etc/yum.conf \
  --destdir=${CENTOS_UPDATE} \
  ${UPDATE_RPM} 2>&1 | grep -v '^looking for' | tee ${BUILD_DIR}/mirror/centos/yumdownloader_update.log

# Yumdownloader/repotrack workaround number one:
# i686 packages are downloaded by mistake. Remove them
rm -rf ${CENTOS_UPDATE}/Packages/*.i686.rpm
# Yumdownloader workaround number two:
# yumdownloader should fail if some packages are missed
test `grep "No Match" ${BUILD_DIR}/mirror/centos/yumdownloader_update.log | wc -l` = 0
# Yumdownloader workaround number three:
# We have exactly four downloading conflicts: django, mysql, kernel-headers and kernel-lt-firmware
#test `grep "conflicts with" ${BUILD_DIR}/mirror/centos/yumdownloader_update.log | grep -v '^[[:space:]]' | wc -l` -le 9
# Yumdownloader workaround number four:
# yumdownloader should fail if some errors appears
test `grep "Errno" ${BUILD_DIR}/mirror/centos/yumdownloader_update.log | wc -l` = 0


# return original version
sed -i "s/${LAST_VERSION}/${PRODUCT_VERSION}/" ${BUILD_DIR}/mirror/centos/etc/yum.repos.d/base.repo

# remove packages that we've already have in main repo
find ${CENTOS_UPDATE} -type f -name "*.rpm" -printf "%f\n" | xargs -i bash -c "test -f ${CENTOS}/{} && rm -f ${CENTOS_UPDATE}/{}"

createrepo --verbose ${CENTOS_UPDATE}/ -o ${CENTOS_UPDATE}/../
