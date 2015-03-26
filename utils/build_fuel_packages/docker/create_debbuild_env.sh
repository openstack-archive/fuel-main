#!/bin/bash

set -ex

# This script will create docker image, that can be used
# for building deb packages

# Some part of the code was adopted from
# https://github.com/docker/docker/blob/master/contrib/mkimage.sh

# docker image name
TAG=fuel/debbuild_env
# packages
SANDBOX_PACKAGES="apt-utils build-essential bzip2 devscripts debhelper fakeroot python-setuptools wget"

PRODUCT_NAME=mos
PRODUCT_VERSION=6.1
MIRROR_BASE=http://mirror.fuel-infra.org/fwm/${PRODUCT_VERSION}

# ubuntu mirror
MIRROR=${UBUNTU_MIRROR:-http://mirror.fuel-infra.org}
UBUNTU_RELEASE=trusty
UBUNTU_MIRROR_SUFFIX=/pkgs/ubuntu

# path where we create our chroot and build docker
TMPDIR=/var/tmp/docker_ubuntu

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

sudo mkdir -p ${rootfsDir}/usr/sbin
sudo bash -c "cat > ${rootfsDir}/usr/sbin/policy-rc.d" <<EOF
#!/bin/sh
# suppress services start in the staging chroots
exit 101
EOF
sudo chmod 755 ${rootfsDir}/usr/sbin/policy-rc.d
sudo mkdir -p ${rootfsDir}/etc/init.d
sudo touch ${rootfsDir}/etc/init.d/.legacy-bootordering

echo "Running debootstrap"
sudo debootstrap --no-check-gpg --arch=amd64 ${UBUNTU_RELEASE} ${rootfsDir} ${MIRROR}${UBUNTU_MIRROR_SUFFIX}

sudo cp /etc/resolv.conf ${rootfsDir}/etc/resolv.conf

echo "Adding build user to sudo"
echo "${BUILD_USER}  ALL=(ALL)       NOPASSWD: ALL" | sudo tee ${rootfsDir}/etc/sudoers.d/build_pkgs

echo "Generating utf8 locale"
sudo chroot ${rootfsDir} /bin/sh -c 'locale-gen en_US.UTF-8; dpkg-reconfigure locales'

echo "Allowing using unsigned repos"
echo "APT::Get::AllowUnauthenticated 1;" | sudo tee ${rootfsDir}/etc/apt/apt.conf.d/02mirantis-unauthenticated

echo "Adding mirrors && Updating apt package database"
sudo bash -c "cat > ${rootfsDir}/etc/apt/source.list" <<EOF
#Upstream Ubuntu mirrors
deb ${MIRROR}${UBUNTU_MIRROR_SUFFIX} ${UBUNTU_RELEASE} main universe multiverse restricted
deb ${MIRROR}${UBUNTU_MIRROR_SUFFIX} ${UBUNTU_RELEASE}-updates main universe multiverse restricted
deb ${MIRROR}${UBUNTU_MIRROR_SUFFIX} ${UBUNTU_RELEASE}-security main universe multiverse restricted
#MOS mirrors
deb ${MIRROR_BASE}/ubuntu ${PRODUCT_NAME}${PRODUCT_VERSION} main restricted
deb ${MIRROR_BASE}/ubuntu ${PRODUCT_NAME}${PRODUCT_VERSION}-security main restricted
deb ${MIRROR_BASE}/ubuntu ${PRODUCT_NAME}${PRODUCT_VERSION}-proposed main restricted
deb ${MIRROR_BASE}/ubuntu ${PRODUCT_NAME}${PRODUCT_VERSION}-updates main restricted
deb ${MIRROR_BASE}/ubuntu ${PRODUCT_NAME}${PRODUCT_VERSION}-holdback main restricted

EOF

sudo bash -c "cat > ${rootfsDir}/etc/apt/preferences.d/fuel" <<EOF
Package: *
Pin: origin download.mirantis.com
Pin-Priority: 1001

Package: *
Pin: release o=Mirantis, n=${UBUNTU_RELEASE}
Pin-Priority: 1101

# to install packages from unmerged fuel-infra requests
Package: *
Pin: release l=${UBUNTU_RELEASE}-fuel-${PRODUCT_VERSION}-stable*
Pin-Priority: 1101

Package: *
Pin: release o=Open Build Service ${UBUNTU_RELEASE}-fuel-${PRODUCT_VERSION}-stable*
Pin-Priority: 1101

EOF

sudo chroot ${rootfsDir} apt-get update && sudo chroot ${rootfsDir} apt-get --yes dist-upgrade

echo "Installing additional packages: ${SANDBOX_PACKAGES})"
test -n "${SANDBOX_PACKAGES}" && sudo chroot ${rootfsDir} apt-get install --yes ${SANDBOX_PACKAGES}
echo "chroot: done"

# put building script in docker
sudo mkdir ${rootfsDir}/opt/sandbox
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
sudo cp ${DIR}/build_deb_in_docker.sh ${rootfsDir}/opt/sandbox

# let's pack rootfs
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
  docker save "${TAG}" | xz > ${ARTS_DIR:-/var/tmp}/fuel-debbuild_env.tar.xz
fi
