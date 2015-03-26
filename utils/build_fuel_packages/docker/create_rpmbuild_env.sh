#!/bin/bash

set -ex

# This script will create docker image, that can be used
# for building rpm packages

# Some part of the code was adopted from
# https://github.com/docker/docker/blob/master/contrib/mkimage.sh

if [ -z ${PRODUCT_VERSION} ]; then
  echo "PRODUCT_VERSION should be defined directly"
  exit -1
fi

# docker image name
TAG=fuel-${PRODUCT_VERSION}/rpmbuild_env
# packages
SANDBOX_PACKAGES="bash git nodejs npm python-setuptools python-pbr ruby rpm-build sudo shadow-utils tar yum yum-utils"

# centos mirror
MIRROR=${CENTOS_MIRROR:-http://mirror.fuel-infra.org/fwm/${PRODUCT_VERSION}/centos/os/x86_64/}

CENTOS_MAJOR=6
CENTOS_MINOR=5
CENTOS_RELEASE="${CENTOS_MAJOR}.${CENTOS_MINOR}"
CENTOS_ARCH=x86_64
# internal mirror
# SANDBOX_MIRROR_CENTOS_UPSTREAM=http://mirrors-local-msk.msk.mirantis.net/centos-${PRODUCT_VERSION}/${CENTOS_RELEASE}
SANDBOX_MIRROR_CENTOS_UPSTREAM="http://vault.centos.org/${CENTOS_RELEASE}"
SANDBOX_MIRROR_CENTOS_UPSTREAM_OS_BASEURL="${SANDBOX_MIRROR_CENTOS_UPSTREAM}/os/${CENTOS_ARCH}/"
SANDBOX_MIRROR_CENTOS_UPDATES_OS_BASEURL="${SANDBOX_MIRROR_CENTOS_UPSTREAM}/updates/${CENTOS_ARCH}"
SANDBOX_MIRROR_EPEL="http://mirror.yandex.ru/epel/"
SANDBOX_MIRROR_EPEL_OS_BASEURL="${SANDBOX_MIRROR_EPEL}/${CENTOS_MAJOR}/${CENTOS_ARCH}/"

# path where we create our chroot and build docker
TMPDIR=/var/tmp/docker_centos

# we need to add user who is going to build packages, usually jenkins
GID=$(id -g)
nGID=$(id -gn)
nUID=$(id -un)

BUILD_USER=${JENKINS_USER:-$nGID}
BUILD_GROUP=${JENKINS_GROUP:-$nUID}
BUILD_UID=${JENKINS_UID:-$GID}
BUILD_GID=${JENKINS_GID:-$UID}

mkdir -p "${TMPDIR}"

# let's make all stuff on tmpfs
sudo mount -n -t tmpfs -o size=2048M docker_chroot "${TMPDIR}"

# creating chroot env
dir="$(mktemp -d ${TMPDIR}/docker-image.XXXXXXXXXX)"

rootfsDir="${dir}/rootfs"
sudo mkdir -p "${rootfsDir}"

# prepare base files
sudo mkdir -p "${rootfsDir}/etc/yum.repos.d"
sudo mkdir -p "${rootfsDir}/etc/yum/pluginconf.d"
sudo mkdir -p "${rootfsDir}/etc/yum-plugins"

sudo tee "${rootfsDir}/etc/yum.conf" <<EOF
[main]
cachedir=/var/cache/yum
keepcache=0
debuglevel=6
logfile=/var/log/yum.log
exclude=*.i686.rpm
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
pluginpath=/etc/yum-plugins
pluginconfpath=/etc/yum/pluginconf.d
reposdir=/etc/yum.repos.d

[Mirantis]
name=Mirantis mirror
baseurl=${MIRROR}
gpgcheck=0
enabled=1
priority=1

[upstream]
name=Upstream mirror
baseurl=${SANDBOX_MIRROR_CENTOS_UPSTREAM_OS_BASEURL}
gpgcheck=0
priority=2

[upstream-updates]
name=Upstream mirror
baseurl=${SANDBOX_MIRROR_CENTOS_UPDATES_OS_BASEURL}
gpgcheck=0
priority=2

[epel]
name=epel mirror
baseurl=${SANDBOX_MIRROR_EPEL_OS_BASEURL}
gpgcheck=0
priority=3

EOF

sudo tee "${rootfsDir}/etc/yum/pluginconf.d/yum-priorities-plugin.conf" <<EOF
[main]
enabled=1
check_obsoletes=1
full_match=1
EOF

sudo curl -sSf https://raw.githubusercontent.com/stackforge/fuel-main/master/mirror/centos/yum-priorities-plugin.py -o \
  "${rootfsDir}/etc/yum-plugins/yum-priorities-plugin.py"

# configure dns
sudo cp /etc/resolv.conf ${rootfsDir}/etc/resolv.conf

yum clean all -c "${rootfsDir}/etc/yum.conf"
# download centos-release
yumdownloader --resolve --archlist=x86_64 \
-c "${rootfsDir}/etc/yum.conf" \
--destdir=${dir} centos-release
sudo rpm -i --root "${rootfsDir}" $(find ${dir} -maxdepth 1 -name "centos-release*rpm" | head -1) || \
echo "centos-release already installed"
sudo rm -f "${rootfsDir}"/etc/yum.repos.d/Cent*
echo 'Rebuilding RPM DB'
sudo rpm --root="${rootfsDir}" --rebuilddb
echo 'Installing packages for Sandbox'
sudo /bin/sh -c "export TMPDIR=${rootfsDir}/tmp/yum TMP=${rootfsDir}/tmp/yum ; \
  yum -c ${rootfsDir}/etc/yum.conf --installroot=${rootfsDir} -y --nogpgcheck install ${SANDBOX_PACKAGES}"

echo "Adding build user to sudo"
echo "${BUILD_USER}  ALL=(ALL)       NOPASSWD: ALL" | sudo tee ${rootfsDir}/etc/sudoers.d/build_pkgs
sudo sed -i 's/requiretty/!requiretty/g' ${rootfsDir}/etc/sudoers

# put building script in docker
sudo mkdir ${rootfsDir}/opt/sandbox
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
sudo cp ${DIR}/build_rpm_in_docker.sh ${rootfsDir}/opt/sandbox

# Docker mounts tmpfs at /dev and procfs at /proc so we can remove them
sudo rm -rf "${rootfsDir}/dev" "${rootfsDir}/proc"
sudo mkdir -p "${rootfsDir}/dev" "${rootfsDir}/proc"

#let's pack rootfs
tarFile="${dir}/rootfs.tar.xz"
sudo touch "${tarFile}"

sudo tar --numeric-owner -caf "${tarFile}" -C "${rootfsDir}" --transform='s,^./,,' .

# prepare for building docker
cat > "${dir}/Dockerfile" <<EOF
FROM scratch
ADD rootfs.tar.xz /

RUN groupadd --gid ${BUILD_GID} ${BUILD_GROUP} && \
    useradd --system --uid ${BUILD_UID} --gid ${BUILD_GID} --home /opt/sandbox --shell /bin/bash ${BUILD_USER} && \
    mkdir -p /opt/sandbox && \
    chown -R ${BUILD_UID}:${BUILD_GID} /opt/sandbox
EOF

# cleaning rootfs
sudo rm -rf "$rootfsDir"

# creating docker image
docker build -t "${TAG}" "${dir}"

# cleaning all
rm -rf "${dir}"
sudo umount "${TMPDIR}"

# saving image
if [ "${SAVE_DOCKER_IMAGE}" == "yes" ]; then
  docker save "${TAG}" | xz > ${ARTS_DIR:-/var/tmp}/fuel-${PRODUCT_VERSION}-rpmbuild_env.tar.xz
fi
