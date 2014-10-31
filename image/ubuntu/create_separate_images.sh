#!/bin/bash
set -x

#NOTE: seems like XFS support won't be implemented due to:
#      1) built-in aggressive pre-allocation which's consuming free space and
#         making impossible to determine the correct size of file system image
#      2) missing fs shrinking method, so only re-creation is possible
#      3) xfsdump/xfsrestore sometimes fails, due to 1) making 2) to fail too

function die { echo "$@" 1>&2 ; exit 1; }

SEPARATE_FS_IMAGES=${SEPARATE_FS_IMAGES:-"/boot,ext2 /,ext4"}

declare -A MOUNT_DICT

for ent in $(echo "$SEPARATE_FS_IMAGES"| tr ' ' '\n'); do
    # expecting '<mountpoint>,<fs_type>'
    arrEnt=(${ent//,/ })
    MOUNT_DICT[${arrEnt[0]}]=${arrEnt[1]}
done

# sort by mount points, eg. / -> /boot -> /var -> /var/lib
MOUNTPOINTS=( $(
    for el in "${!MOUNT_DICT[@]}"
    do
        echo "$el"
    done | sort) )

# create additional loop_devices
FUEL_DEVICE_PREFIX=loop_devices_fuel_build
TMP_BUILD_DIR=${TMP_BUILD_DIR:-/tmp/fuel_img}
TMP_BUILD_IMG_DIR=${TMP_BUILD_IMG_DIR:-$TMP_BUILD_DIR/imgs}
TMP_CHROOT_DIR=${TMP_CHROOT_DIR:-$TMP_BUILD_DIR/chroot}
SPARSE_FILE_INITIAL_SIZE=2G
SPARSE_IMG_FILE_SUFFIX=sparse_img
IMG_ENDING=img
IMG_PREFIX=${IMG_PREFIX:-ubuntu}
IMG_SUFFIX=${IMG_SUFFIX:-1204_amd64}
LOOP_DEVICES_MAJOR=7
LOOP_DEVICES_MINOR_INITIAL=10
LOCAL_MIRROR=${LOCAL_MIRROR:-'/tmp/mirror'}
DEBOOTSTRAP_PARAMS=${DEBOOTSTRAP_PARAMS:-''}
INSTALL_PACKAGES=${INSTALL_PACKAGES:-''}

if [ ! -d "$TMP_BUILD_DIR" ]; then
    mkdir -p "$TMP_BUILD_DIR" || die "Couldn't create directory"
fi

if [ ! -d "$TMP_BUILD_IMG_DIR" ]; then
    mkdir -p "$TMP_BUILD_IMG_DIR" || die "Couldn't create directory"
fi

if [ ! -d "$TMP_CHROOT_DIR" ]; then
    mkdir -p "$TMP_CHROOT_DIR" || die "Couldn't create directory"
fi

# try to remove stale files
for idx in $(seq $((${#MOUNTPOINTS[@]} - 1)) -1 0); do
    MOUNT_POINT=${MOUNTPOINTS[$idx]}

    if [ "$MOUNT_POINT" == "/" ]; then
        MOUNT_POINT=""
    fi

    IMG_FILE_NAME=${TMP_BUILD_IMG_DIR}/${IMG_PREFIX}_${IMG_SUFFIX}$(echo $MOUNT_POINT | tr '/' '-').${IMG_ENDING}
    SPARSE_FILE_NAME=${IMG_FILE_NAME}.${SPARSE_IMG_FILE_SUFFIX}
    LOOP_DEV=/dev/${FUEL_DEVICE_PREFIX}${idx}
    if mount | grep -q "${TMP_CHROOT_DIR}${MOUNT_POINT}"; then
        sudo umount ${TMP_CHROOT_DIR}${MOUNT_POINT} || echo "Couldn't umnount old loop-device file, trying to perform lazy umnount"
        if [ $? -ne 0 ]; then
            sudo umount -l ${TMP_CHROOT_DIR}${MOUNT_POINT} || echo "Couldn't unmount old loop-device file"
        fi
    fi
    if [ -e "$LOOP_DEV" ]; then
        # try to remove if it exists
        sudo losetup -d $LOOP_DEV || die "Couldn't dissociate old loop-device file"
        sudo rm -f $LOOP_DEV || die "Couldn't remove old loop-device file"
        sudo rm -f ${SPARSE_FILE_NAME} || die "Could remove old sparce image"
    fi
done

for idx in $(seq 0 $((${#MOUNTPOINTS[@]} - 1)) ); do
    MOUNT_POINT=${MOUNTPOINTS[$idx]}

    if [ "$MOUNT_POINT" == "/" ]; then
        MOUNT_POINT=""
    fi

    IMG_FILE_NAME=${TMP_BUILD_IMG_DIR}/${IMG_PREFIX}_${IMG_SUFFIX}$(echo $MOUNT_POINT | tr '/' '-').${IMG_ENDING}
    SPARSE_FILE_NAME=${IMG_FILE_NAME}.${SPARSE_IMG_FILE_SUFFIX}
    MOUNT_POINT=${MOUNTPOINTS[$idx]}
    LOOP_DEV=/dev/${FUEL_DEVICE_PREFIX}${idx}

    truncate -s ${SPARSE_FILE_INITIAL_SIZE} ${SPARSE_FILE_NAME} || die "Couldn't create sparse file"

    # create loop device
    sudo mknod -m 660 ${LOOP_DEV} b ${LOOP_DEVICES_MAJOR} $(( $LOOP_DEVICES_MINOR_INITIAL + $idx )) || die "Couldn't create loop-device file"
    sudo losetup ${LOOP_DEV} ${SPARSE_FILE_NAME} || die "Couldn't associate loop-device file"

    FS_TYPE=${MOUNT_DICT[$MOUNT_POINT]}
    if [ "$FS_TYPE" == "ext2" ]; then
        sudo mkfs.ext2 -F ${LOOP_DEV} || die "Couldn't create filesystem"
    elif [ "$FS_TYPE" == "ext3" ]; then
        sudo mkfs.ext3 -F ${LOOP_DEV} || die "Couldn't create filesystem"
    elif [ "$FS_TYPE" == "ext4" ]; then
        sudo mkfs.ext4 -F ${LOOP_DEV} || die "Couldn't create filesystem"
    else
        echo "Unsupported fs type $FS_TYPE. Exitting now!"
        exit 1
    fi
done

for idx in $(seq 0 $((${#MOUNTPOINTS[@]} - 1)) ); do
    MOUNT_POINT=${MOUNTPOINTS[$idx]}
    LOOP_DEV=/dev/${FUEL_DEVICE_PREFIX}${idx}
    sudo mkdir -p ${TMP_CHROOT_DIR}${MOUNT_POINT} || die "Could create directory"
    sudo mount ${LOOP_DEV} ${TMP_CHROOT_DIR}${MOUNT_POINT} || die "Couldn't mount mountpoint"
done

# install base system
sudo debootstrap $DEBOOTSTRAP_PARAMS || die "Couldn't finish debootstrap successfully"

#inject hardcoded root password `r00tme`
sudo sed -i 's%root:[\*,\!]%root:$6$IInX3Cqo$5xytL1VZbZTusOewFnG6couuF0Ia61yS3rbC6P5YbZP2TYclwHqMq9e3Tg8rvQxhxSlBXP1DZhdUamxdOBXK0.%' ${TMP_CHROOT_DIR}/etc/shadow

echo 'APT::Get::AllowUnauthenticated 1;' | sudo tee ${TMP_CHROOT_DIR}/etc/apt/apt.conf.d/02mirantis-unauthenticated

#local mirror
sudo mkdir -p ${TMP_CHROOT_DIR}/tmp/mirror
sudo mount --bind ${LOCAL_MIRROR} ${TMP_CHROOT_DIR}/tmp/mirror
echo "deb file:///tmp/mirror/ubuntu precise main" | sudo tee ${TMP_CHROOT_DIR}/etc/apt/sources.list
sudo chroot ${TMP_CHROOT_DIR} apt-get update
sudo chroot ${TMP_CHROOT_DIR} apt-get -y install ${INSTALL_PACKAGES}
sudo umount ${TMP_CHROOT_DIR}/tmp/mirror

#cloud-init reconfigure to use NoCloud data source
echo "cloud-init cloud-init/datasources multiselect NoCloud, None" | sudo chroot ${TMP_CHROOT_DIR} debconf-set-selections -v
sudo chroot ${TMP_CHROOT_DIR} dpkg-reconfigure -f noninteractive cloud-init

for idx in $(seq $((${#MOUNTPOINTS[@]} - 1)) -1 0); do
    MOUNT_POINT=${MOUNTPOINTS[$idx]}
    if [ "$MOUNT_POINT" == "/" ]; then
        MOUNT_POINT=""
    fi
    IMG_FILE_NAME=${TMP_BUILD_IMG_DIR}/${IMG_PREFIX}_${IMG_SUFFIX}$(echo $MOUNT_POINT | tr '/' '-').${IMG_ENDING}
    MOUNT_POINT=${MOUNTPOINTS[$idx]}
    SPARSE_FILE_NAME=${IMG_FILE_NAME}.${SPARSE_IMG_FILE_SUFFIX}
    LOOP_DEV=/dev/${FUEL_DEVICE_PREFIX}${idx}
    FS_TYPE=${MOUNT_DICT[$MOUNT_POINT]}

    sudo umount ${LOOP_DEV} || die "Couldn't unmount mountpoint"

    if [ "$FS_TYPE" == "ext2" ] || [ "$FS_TYPE" == "ext3" ] || [ "$FS_TYPE" == "ext4" ]; then
        sudo e2fsck -yf ${LOOP_DEV} || die "Couldn't check filesystem"
        sudo resize2fs -F -M ${LOOP_DEV} || die "Couldn't resize filesystem"
        # calculate fs size precisely
        BLOCK_COUNT=$(sudo dumpe2fs -h ${LOOP_DEV} | grep 'Block count' | awk '{print $3}')
        BLOCK_SIZE=$(sudo dumpe2fs -h ${LOOP_DEV} | grep 'Block size' | awk '{print $3}')
        BLOCK_K_SIZE=$(( $BLOCK_SIZE / 1024 ))
        BLOCK_K_COUNT=$(( 1 + $BLOCK_COUNT / 1024 ))
        EXPECTED_M_SIZE=$(( $BLOCK_K_COUNT * $BLOCK_K_SIZE ))
        sudo dd if=${LOOP_DEV} of=${IMG_FILE_NAME} bs=1M count=${EXPECTED_M_SIZE} || die "Couldn't copy image"
    else
        echo "Unsupported fs type $FS_TYPE. Exitting now!"
        exit 1
    fi
    sudo chmod a+r ${IMG_FILE_NAME} || die "Couldn't grant reading access to image file"
    python ./image/ubuntu/add_image_to_profile.py --filename $(basename $IMG_FILE_NAME).gz --format ${FS_TYPE} --container gzip --mountpoint ${MOUNT_POINT} -O ${TMP_BUILD_IMG_DIR}/profile.yaml
    sudo losetup -d ${LOOP_DEV} || die "Couldn't dissociate loop-device file"
    sudo rm -f ${LOOP_DEV} || die "Couldn't remove loop-device file"
    rm ${SPARSE_FILE_NAME} || die "Couldn't remove sparse image file"
done
