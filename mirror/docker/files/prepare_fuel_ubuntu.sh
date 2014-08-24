#!/bin/bash -x

# This script will create docker base image, that can be used
# for creating ubuntu mirror and building deb packages
# This script and ubuntu env should be universal as much as possible
# and shouldn't depend on Make process.

# Some part of the code was adopted from
# https://github.com/docker/docker/blob/master/contrib/mkimage.sh

# docker image name
TAG=fuel/ubuntu
# path where we create our chroot and build docker
dir=

if [ -z $1 ]; then
  echo "Please, provide path to multistrap.conf file"
  exit 1
fi

MULTISTRAP_CONF=$1

# creating chroot env
if [ -z "${dir}" ]; then
  dir="$(mktemp -d ${TMPDIR:-/var/tmp}/docker-mkimage.XXXXXXXXXX)"
fi

rootfsDir="${dir}/rootfs"
sudo mkdir -p "${rootfsDir}"

# run multistrap
sudo mkdir -p "${rootfsDir}/proc"
sudo mount -t proc none "${rootfsDir}/proc"
sudo multistrap -a amd64  -f "${MULTISTRAP_CONF}" -d "${rootfsDir}"
sudo chroot "${rootfsDir}" /bin/bash -c "dpkg --configure -a || exit 0"
sudo chroot "${rootfsDir}" /bin/bash -c "rm -rf /var/run/*"
sudo chroot "${rootfsDir}" /bin/bash -c "dpkg --configure -a || exit 0"
sudo umount "${rootfsDir}/proc"
sudo rm -f "${rootfsDir}"/etc/apt/sources.list.d/*.list

# Docker mounts tmpfs at /dev and procfs at /proc so we can remove them
sudo rm -rf "${rootfsDir}/dev" "${rootfsDir}/proc"
sudo mkdir -p "${rootfsDir}/dev" "${rootfsDir}/proc"

# let's put dns
echo -e "nameserver 8.8.8.8\nnameserver 8.8.4.4" | sudo tee "${rootfsDir}/etc/resolv.conf"

# let's pack rootfs
tarFile="${dir}/rootfs.tar.xz"
sudo touch "${tarFile}"

sudo tar --numeric-owner -caf "${tarFile}" -C "${rootfsDir}" --transform='s,^./,,' .

# prepare for building docker
cat > "${dir}/Dockerfile" <<'EOF'
FROM scratch
ADD rootfs.tar.xz /
EOF

# cleaning rootfs
sudo rm -rf "$rootfsDir"

# creating docker image
docker build -t "${TAG}" "${dir}"

# cleaning all
rm -rf "${dir}"

# saving image
docker save "${TAG}" | pxz > /var/tmp/fuel-ubuntu.tar.xz

# clearing docker env
docker rmi scratch
docker rmi "${TAG}"
