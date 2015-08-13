#!/bin/bash

set -ex

# This script will create docker image, that can be used
# for building deb packages

# Some part of the code was adopted from
# https://github.com/docker/docker/blob/master/contrib/mkimage.sh

if [ -z ${PRODUCT_VERSION} ]; then
  echo "PRODUCT_VERSION should be defined directly"
  exit -1
fi

# product
PRODUCT_NAME=mos
# upstream mirror
MIRROR_UBUNTU=${UBUNTU_MIRROR:-http://mirror.fuel-infra.org}
MIRROR_UBUNTU_ROOT=${UBUNTU_MIRROR_SUFFIX:-/pkgs/ubuntu}
UBUNTU_RELEASE=trusty
MIRROR_UBUNTU_SUITE=${UBUNTU_RELEASE}
MIRROR_UBUNTU_SECTION="main universe multiverse restricted"
#MOS mirror
MIRROR_MOS_UBUNTU="${MIRROR_UBUNTU}"
MIRROR_MOS_UBUNTU_ROOT="/mos-repos/ubuntu/${PRODUCT_VERSION}"
MIRROR_MOS_UBUNTU_SUITE="${PRODUCT_NAME}${PRODUCT_VERSION}"
MIRROR_MOS_UBUNTU_SECTION="main restricted"

# docker image name
TAG=fuel-${PRODUCT_VERSION}/debbuild_env
# packages
SANDBOX_PACKAGES="apt-utils build-essential bzip2 devscripts debhelper fakeroot python-pbr python-setuptools wget"


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
sudo bash -c "cat > ${TMPDIR}/policy-rc.d" <<EOF
#!/bin/sh
# suppress services start in the staging chroots
exit 101
EOF
sudo chmod 755 ${TMPDIR}/policy-rc.d
sudo mkdir -p ${rootfsDir}/etc/init.d
sudo touch ${rootfsDir}/etc/init.d/.legacy-bootordering
sudo mkdir -p ${rootfsDir}/usr/sbin
sudo cp -a ${TMPDIR}/policy-rc.d ${rootfsDir}/usr/sbin

echo "Running debootstrap"
sudo debootstrap --no-check-gpg --arch=amd64 ${UBUNTU_RELEASE} ${rootfsDir} ${MIRROR_UBUNTU}${MIRROR_UBUNTU_ROOT}

sudo cp /etc/resolv.conf ${rootfsDir}/etc/resolv.conf

echo "Adding build user to sudo"
echo "${BUILD_USER}  ALL=(ALL)       NOPASSWD: ALL" | sudo tee ${rootfsDir}/etc/sudoers.d/build_pkgs

echo "Generating utf8 locale"
sudo chroot ${rootfsDir} /bin/sh -c 'locale-gen en_US.UTF-8; dpkg-reconfigure -f noninteractive locales'

sudo cp -a ${TMPDIR}/policy-rc.d ${rootfsDir}/usr/sbin
echo "Allowing using unsigned repos"
echo "APT::Get::AllowUnauthenticated 1;" | sudo tee ${rootfsDir}/etc/apt/apt.conf.d/02mirantis-unauthenticated

echo "Adding mirrors && Updating apt package database"
sudo bash -c "cat > ${rootfsDir}/etc/apt/sources.list" <<EOF
#Upstream Ubuntu mirrors
deb ${MIRROR_UBUNTU}${MIRROR_UBUNTU_ROOT} ${MIRROR_UBUNTU_SUITE} ${MIRROR_UBUNTU_SECTION}
deb ${MIRROR_UBUNTU}${MIRROR_UBUNTU_ROOT} ${MIRROR_UBUNTU_SUITE}-updates ${MIRROR_UBUNTU_SECTION}
deb ${MIRROR_UBUNTU}${MIRROR_UBUNTU_ROOT} ${MIRROR_UBUNTU_SUITE}-security ${MIRROR_UBUNTU_SECTION}
# MOS repos
deb ${MIRROR_MOS_UBUNTU}${MIRROR_MOS_UBUNTU_ROOT} ${MIRROR_MOS_UBUNTU_SUITE} ${MIRROR_MOS_UBUNTU_SECTION}
deb ${MIRROR_MOS_UBUNTU}${MIRROR_MOS_UBUNTU_ROOT} ${MIRROR_MOS_UBUNTU_SUITE}-security ${MIRROR_MOS_UBUNTU_SECTION}
deb ${MIRROR_MOS_UBUNTU}${MIRROR_MOS_UBUNTU_ROOT} ${MIRROR_MOS_UBUNTU_SUITE}-proposed ${MIRROR_MOS_UBUNTU_SECTION}
deb ${MIRROR_MOS_UBUNTU}${MIRROR_MOS_UBUNTU_ROOT} ${MIRROR_MOS_UBUNTU_SUITE}-updates ${MIRROR_MOS_UBUNTU_SECTION}
deb ${MIRROR_MOS_UBUNTU}${MIRROR_MOS_UBUNTU_ROOT} ${MIRROR_MOS_UBUNTU_SUITE}-holdback ${MIRROR_MOS_UBUNTU_SECTION}

EOF

sudo bash -c "cat > ${rootfsDir}/etc/apt/preferences.d/fuel" <<EOF
Package: *
Pin: release o=Mirantis, n=${MIRROR_UBUNTU_SUITE}
Pin-Priority: 1101

Package: *
Pin: release o=Mirantis, n=${PRODUCT_NAME}${PRODUCT_VERSION}
Pin-Priority: 1101

# to install packages from unmerged fuel-infra requests
Package: *
Pin: release l=${UBUNTU_RELEASE}-fuel-${PRODUCT_VERSION}-stable*
Pin-Priority: 1101

Package: *
Pin: release o=Open Build Service ${UBUNTU_RELEASE}-fuel-${PRODUCT_VERSION}-stable*
Pin-Priority: 1101

EOF

sudo chroot ${rootfsDir} apt-get update && sudo chroot ${rootfsDir} \
  env DEBIAN_FRONTEND=noninteractive \
  DEBCONF_NONINTERACTIVE_SEEN=true \
  LC_ALL=C LANG=C LANGUAGE=C \
  apt-get --yes dist-upgrade

echo "Installing additional packages: ${SANDBOX_PACKAGES})"
test -n "${SANDBOX_PACKAGES}" && sudo chroot ${rootfsDir} \
  env DEBIAN_FRONTEND=noninteractive \
  DEBCONF_NONINTERACTIVE_SEEN=true \
  LC_ALL=C LANG=C LANGUAGE=C \
  apt-get install --yes ${SANDBOX_PACKAGES}
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
  docker save "${TAG}" | xz > ${ARTS_DIR:-/var/tmp}/fuel-${PRODUCT_VERSION}-debbuild_env.tar.xz
fi
