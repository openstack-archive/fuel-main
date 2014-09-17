#!/bin/bash
set -x

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
SPARSE_FILE_INITIAL_SIZE=1G
SPARSE_IMG_FILE_SUFFIX=sparse_img
IMG_ENDING=img
IMG_PREFIX=${IMG_PREFIX:-ubuntu}
IMG_SUFFIX=${IMG_SUFFIX:-1204_amd64}
OVERSIZED_PERCENTAGE=35
LOOP_DEVICES_MAJOR=7
LOOP_DEVICES_MINOR_4_XFS_REBUILD=9
LOOP_DEVICES_MINOR_INITIAL=10
BACKUP_FILE_NAME=backup.tar
DEBOOTSRAP_PARAMS=${DEBOOTSRAP_PARAMS:-''}

if [ ! -d "$TMP_BUILD_DIR" ]; then
    mkdir -p "$TMP_BUILD_DIR"
fi

if [ ! -d "$TMP_BUILD_IMG_DIR" ]; then
    mkdir -p "$TMP_BUILD_IMG_DIR"
fi

if [ ! -d "$TMP_CHROOT_DIR" ]; then
    mkdir -p "$TMP_CHROOT_DIR"
fi

for idx in $(seq 0 $((${#MOUNTPOINTS[@]} - 1)) ); do
    MOUNT_POINT=${MOUNTPOINTS[$idx]}

    if [ "$MOUNT_POINT" == "/" ]; then
        MOUNT_POINT=""
    fi

    IMG_FILE_NAME=${TMP_BUILD_IMG_DIR}/${IMG_PREFIX}_${IMG_SUFFIX}$(echo $MOUNT_POINT | tr '/' '-').${IMG_ENDING}
    SPARSE_FILE_NAME=${IMG_FILE_NAME}.${SPARSE_IMG_FILE_SUFFIX}
    MOUNT_POINT=${MOUNTPOINTS[$idx]}

    truncate -s ${SPARSE_FILE_INITIAL_SIZE} ${SPARSE_FILE_NAME} 

    LOOP_DEV=/dev/${FUEL_DEVICE_PREFIX}${idx}
    if [ -f "$FILE" ]; then
        # try to remove if it exists
        sudo losetup -d $LOOP_DEV
        sudo rm -f $LOOP_DEV
    fi
    # create loop device
    sudo mknod -m 660 ${LOOP_DEV} b ${LOOP_DEVICES_MAJOR} $(( $LOOP_DEVICES_MINOR_INITIAL + $idx ))
    sudo losetup ${LOOP_DEV} ${SPARSE_FILE_NAME} 

    FS_TYPE=${MOUNT_DICT[$MOUNT_POINT]}
    if [ "$FS_TYPE" == "ext2" ]; then
        sudo mkfs.ext2 -F ${LOOP_DEV}
    elif [ "$FS_TYPE" == "ext3" ]; then
        sudo mkfs.ext3 -F ${LOOP_DEV}
    elif [ "$FS_TYPE" == "ext4" ]; then
        sudo mkfs.ext4 -F ${LOOP_DEV}
    elif [ "$FS_TYPE" == "xfs" ]; then
        sudo mkfs.xfs -f ${LOOP_DEV}
    else
        echo "Unsupported fs type $FS_TYPE. Exitting now!"
        exit 1
    fi
done

for idx in $(seq 0 $((${#MOUNTPOINTS[@]} - 1)) ); do
    MOUNT_POINT=${MOUNTPOINTS[$idx]}
    LOOP_DEV=/dev/${FUEL_DEVICE_PREFIX}${idx}
    sudo mkdir -p ${TMP_CHROOT_DIR}${MOUNT_POINT}
    sudo mount ${LOOP_DEV} ${TMP_CHROOT_DIR}${MOUNT_POINT}
done

sudo debootstrap $DEBOOTSRAP_PARAMS

for idx in $(seq $((${#MOUNTPOINTS[@]} - 1)) -1 0); do
    MOUNT_POINT=${MOUNTPOINTS[$idx]}
    if [ "$MOUNT_POINT" == "/" ]; then
        MOUNT_POINT=""
    fi
    IMG_FILE_NAME=${TMP_BUILD_IMG_DIR}/${IMG_PREFIX}_${IMG_SUFFIX}$(echo $MOUNT_POINT | tr '/' '-').${IMG_ENDING}
    MOUNT_POINT=${MOUNTPOINTS[$idx]}
    SPARSE_FILE_NAME=${IMG_FILE_NAME}.${SPARSE_IMG_FILE_SUFFIX}
    LOOP_DEV=/dev/${FUEL_DEVICE_PREFIX}${idx}
    
    M_SIZE=$(sudo du -m ${TMP_CHROOT_DIR}/${MOUNT_POINT} 2>&1 | tail -n1 | cut -d $'\t' -f1)
    FS_TYPE=${MOUNT_DICT[$MOUNT_POINT]}
    EXPECTED_M_SIZE=$(( M_SIZE * (100 + $OVERSIZED_PERCENTAGE) / 100 ))

    if [ "$FS_TYPE" != "xfs" ]; then
        sudo umount ${LOOP_DEV}
    else
        if [ "$EXPECTED_M_SIZE" -lt "100" ]; then
            EXPECTED_M_SIZE=$(( $EXPECTED_M_SIZE * 2 ))
        fi
    fi

    if [ "$FS_TYPE" == "ext2" ] || [ "$FS_TYPE" == "ext3" ] || [ "$FS_TYPE" == "ext4" ]; then
        sudo e2fsck -f ${LOOP_DEV}
        sudo resize2fs -F -M ${LOOP_DEV}
        sudo dd if=${LOOP_DEV} of=${IMG_FILE_NAME} bs=1M count=${EXPECTED_M_SIZE}
    elif [ "$FS_TYPE" == "xfs" ]; then
        # backup contents
        sudo tar cf ${BACKUP_FILE_NAME} -C ${TMP_CHROOT_DIR}${MOUNT_POINT} .
        sudo umount -l ${LOOP_DEV}
        sudo losetup -d ${LOOP_DEV}
        # since there's no way to shrink xfs so just recreating it
        truncate -s ${EXPECTED_M_SIZE}M ${SPARSE_FILE_NAME}.new
        # create loop device
        sudo losetup ${LOOP_DEV} ${SPARSE_FILE_NAME}.new
        sudo mkfs.xfs -f ${LOOP_DEV}
        sudo mkdir -p ${TMP_CHROOT_DIR}${MOUNT_POINT}.new
        sudo mount ${LOOP_DEV} ${TMP_CHROOT_DIR}${MOUNT_POINT}.new
        # copy directory content
        sudo tar xf ${BACKUP_FILE_NAME} -C ${TMP_CHROOT_DIR}${MOUNT_POINT}.new
        sudo rm ${BACKUP_FILE_NAME}
        # do lazy umount to avoid 'device is busy' errors
        sudo umount -l ${LOOP_DEV}
        mv ${SPARSE_FILE_NAME}.new ${SPARSE_FILE_NAME}
        # unsparse the file
        cp --sparse=never ${SPARSE_FILE_NAME} ${IMG_FILE_NAME}
    else
        echo "Unsupported fs type $FS_TYPE. Exitting now!"
        exit 1
    fi
    sudo chmod a+r ${IMG_FILE_NAME}
    sudo losetup -d ${LOOP_DEV}
    sudo rm -f ${LOOP_DEV}
    rm ${SPARSE_FILE_NAME}
done
