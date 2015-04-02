#!/bin/bash
set -x

#NOTE: seems like XFS support won't be implemented due to:
#      1) built-in aggressive pre-allocation which's consuming free space and
#         making impossible to determine the correct size of file system image
#      2) missing fs shrinking method, so only re-creation is possible
#      3) xfsdump/xfsrestore sometimes fails, due to 1) making 2) to fail too

function die_ret { echo "$@" 1>&2 ; return 1; }
function die { echo "$@" 1>&2 ; exit 1; }

SEPARATE_FS_IMAGES=${SEPARATE_FS_IMAGES:-"/boot,ext2 /,ext4"}

declare -A MOUNT_DICT
declare -a LOOP_DEVICES_LIST
for ent in $(echo "$SEPARATE_FS_IMAGES"| tr ' ' '\n'); do
    # expecting '<mountpoint>,<fs_type>'
    arrEnt=(${ent//,/ })
    MOUNT_DICT[${arrEnt[0]}]=${arrEnt[1]}
done

declare -A IMAGES_NAMES_DICT

for ent in $(echo "$SEPARATE_FS_IMAGES_NAMES"| tr ' ' '\n'); do
    # expecting '<mountpoint>,<image_name>'
    arrEnt=(${ent//,/ })
    IMAGES_NAMES_DICT[${arrEnt[0]}]=${arrEnt[1]}
done

# sort by mount points, eg. / -> /boot -> /var -> /var/lib
MOUNTPOINTS=( $(
    for el in "${!MOUNT_DICT[@]}"
    do
        echo "$el"
    done | sort) )

# create additional loop_devices
FUEL_DEVICE_PREFIX=loop
MAX_DOWNLOAD_ATTEMPTS=${MAX_DOWNLOAD_ATTEMPTS:-10}
UBUNTU_MAJOR=${UBUNTU_MAJOR:-12}
UBUNTU_MINOR=${UBUNTU_MINOR:-04}
UBUNTU_ARCH=${UBUNTU_ARCH:-amd64}
UBUNTU_RELEASE=${UBUNTU_RELEASE:-precise}
TMP_BUILD_DIR=`mktemp -d`
echo "${TMP_BUILD_DIR} is used as temprorary directory for building images"
TMP_BUILD_IMG_DIR=${TMP_BUILD_IMG_DIR:-$TMP_BUILD_DIR/imgs}
TMP_CHROOT_DIR=${TMP_CHROOT_DIR:-$TMP_BUILD_DIR/chroot}
BASE_MIRROR_URL=$(echo "$UBUNTU_BASE_MIRROR" | cut -d '|' -f4-)
DST_DIR=${DST_DIR:-/var/www/nailgun}
SPARSE_FILE_INITIAL_SIZE=2G
SPARSE_IMG_FILE_SUFFIX=sparse_img
IMG_ENDING=img
IMG_PREFIX=${IMG_PREFIX:-ubuntu}
if [ -z "$IMG_SUFFIX" ]; then
    IMG_SUFFIX="${UBUNTU_MAJOR}${UBUNTU_MINOR}_${UBUNTU_ARCH}"
fi
LOOP_DEVICES_MAJOR=7
LOOP_DEVICES_MINOR_INITIAL=10
DEBOOTSTRAP_PARAMS=${DEBOOTSTRAP_PARAMS:-"--no-check-gpg --arch=$UBUNTU_ARCH $UBUNTU_RELEASE $TMP_CHROOT_DIR"}
UBUNTU_KERNEL_FLAVOR=${UBUNTU_KERNEL_FLAVOR:-lts-trusty}
INSTALL_PACKAGES=${INSTALL_PACKAGES:-"
bash-completion
curl
daemonize
build-essential
gdisk
grub-pc
linux-firmware
linux-firmware-nonfree
linux-image-generic-$UBUNTU_KERNEL_FLAVOR
linux-headers-generic-$UBUNTU_KERNEL_FLAVOR
lvm2
mdadm
nailgun-agent
nailgun-mcagents
nailgun-net-check
ntp
openssh-client
openssh-server
telnet
ubuntu-minimal
ubuntu-standard
virt-what
acl
anacron
bridge-utils
bsdmainutils
cloud-init
debconf-utils
libaugeas-ruby
libstomp-ruby1.8
libshadow-ruby1.8
libjson-ruby1.8
mcollective
puppet
python-amqp
ruby-ipaddress
ruby-netaddr
ruby-openstack
ruby-stomp
vim
vlan
uuid-runtime"}


function make_dirs {
    if [ ! -d "$TMP_BUILD_DIR" ]; then
        mkdir -p "$TMP_BUILD_DIR" || die_ret "Couldn't create directory"
    fi

    if [ ! -d "$TMP_BUILD_IMG_DIR" ]; then
        mkdir -p "$TMP_BUILD_IMG_DIR" || die_ret "Couldn't create directory"
    fi

    if [ ! -d "$TMP_CHROOT_DIR" ]; then
        mkdir -p "$TMP_CHROOT_DIR" || die_ret "Couldn't create directory"
    fi

    if [ ! -d "$DST_DIR" ]; then
        mkdir -p "$DST_DIR" || die_ret "Couldn't create directory"
    fi
    return 0
}

function delete_dirs {
    if [ -d "$TMP_CHROOT_DIR" ]; then
        rm -fr "$TMP_CHROOT_DIR" || die_ret "Couldn't delete directory"
    fi

    if [ -d "$TMP_BUILD_IMG_DIR" ]; then
        rm -fr "$TMP_BUILD_IMG_DIR" || die_ret "Couldn't delete directory"
    fi

    if [ -d "$TMP_BUILD_DIR" ]; then
        rm -fr "$TMP_BUILD_DIR" || die_ret "Couldn't delete directory"
    fi
    return 0
}

function cleanup {
    clean_chroot
    if mountpoint -q ${TMP_CHROOT_DIR}/proc; then
        umount -l ${TMP_CHROOT_DIR}/proc || true
    fi

    for idx in $(seq $((${#MOUNTPOINTS[@]} - 1)) -1 0); do
        MOUNT_POINT=${MOUNTPOINTS[$idx]}

        if [ "$MOUNT_POINT" == "/" ]; then
            MOUNT_POINT=""
        fi

        IMG_FILE_NAME=${TMP_BUILD_IMG_DIR}/${IMG_PREFIX}_${IMG_SUFFIX}$(echo $MOUNT_POINT | tr '/' '-').${IMG_ENDING}
        SPARSE_FILE_NAME=${IMG_FILE_NAME}.${SPARSE_IMG_FILE_SUFFIX}
        if [ ${#LOOP_DEVICES_LIST[@]} -gt 0 ]; then
            LOOP_DEV=${LOOP_DEVICES_LIST[$idx]}
            if ! umount_try_harder "${TMP_CHROOT_DIR}${MOUNT_POINT}"; then
                umount -l "${TMP_CHROOT_DIR}${MOUNT_POINT}" || die_ret "Failed to umount $LOOP_DEV (${TMP_CHROOT_DIR}${MOUNT_POINT})"
            fi
            if ! losetup -d "$LOOP_DEV"; then
                echo "Warning: unable to detach loop device $LOOP_DEV"
            fi
        fi
        if [ -e "$SPARSE_FILE_NAME" ]; then
            rm -f ${SPARSE_FILE_NAME} || die_ret "Couldn't remove old sparce image"
        fi
    done
    delete_dirs || die_ret "Couldn't remove dirs"
    return 0
}

function precreate_loop_devices {
    for x in $(seq 0 7); do
        local loop_dev=/dev/${FUEL_DEVICE_PREFIX}${x}
        if [ ! -e "$loop_dev" ]; then
            mknod -m 660 ${loop_dev} b ${LOOP_DEVICES_MAJOR} ${x} || die_ret "Couldn't create loop-device file"
        fi
    done
    return 0
}

function allocate_loop_device {
    local sparse_file="$1"
    local loop_count=8
    local max_loop_count=255
    local loop_dev=''
    while [ -z "$loop_dev" ]; do
        for minor in `seq 0 $loop_count`; do
            local cur_loop="/dev/${FUEL_DEVICE_PREFIX}${minor}"
            [ -b "$cur_loop" ] || mknod -m 660 "$cur_loop" b $LOOP_DEVICES_MAJOR $minor
        done
        [ $loop_count -ge $max_loop_count ] && die_ret "too many loopback devices"
        loop_count=$((loop_count*2))
        loop_dev=`losetup --find`
    done
    LOOP_DEVICES_LIST+=(${loop_dev})
    losetup ${loop_dev} ${sparse_file} || die_ret "Couldn't associate loop-device file"
    return 0
}

function create_loop_device_and_makefs {
    for idx in $(seq 0 $((${#MOUNTPOINTS[@]} - 1)) ); do
        MOUNT_POINT=${MOUNTPOINTS[$idx]}

        if [ "$MOUNT_POINT" == "/" ]; then
            MOUNT_POINT=""
        fi

        IMG_FILE_NAME=${TMP_BUILD_IMG_DIR}/${IMG_PREFIX}_${IMG_SUFFIX}$(echo $MOUNT_POINT | tr '/' '-').${IMG_ENDING}
        SPARSE_FILE_NAME=${IMG_FILE_NAME}.${SPARSE_IMG_FILE_SUFFIX}
        MOUNT_POINT=${MOUNTPOINTS[$idx]}

        truncate -s ${SPARSE_FILE_INITIAL_SIZE} ${SPARSE_FILE_NAME} || die_ret "Couldn't create sparse file"

        allocate_loop_device ${SPARSE_FILE_NAME} || die_ret "Couldn't allocate loop-device file"

        LOOP_DEV=${LOOP_DEVICES_LIST[$idx]}

        FS_TYPE=${MOUNT_DICT[$MOUNT_POINT]}
        if [ "$FS_TYPE" == "ext2" ]; then
            mkfs.ext2 -F ${LOOP_DEV} || die_ret "Couldn't create filesystem"
        elif [ "$FS_TYPE" == "ext3" ]; then
            mkfs.ext3 -F ${LOOP_DEV} || die_ret "Couldn't create filesystem"
        elif [ "$FS_TYPE" == "ext4" ]; then
            mkfs.ext4 -F ${LOOP_DEV} || die_ret "Couldn't create filesystem"
        else
            echo "Unsupported fs type $FS_TYPE. Exitting now!"
            return 1
        fi
    done
    return 0
}

function do_mounts {
    for idx in $(seq 0 $((${#MOUNTPOINTS[@]} - 1)) ); do
        MOUNT_POINT=${MOUNTPOINTS[$idx]}
        LOOP_DEV=${LOOP_DEVICES_LIST[$idx]}
        mkdir -p ${TMP_CHROOT_DIR}${MOUNT_POINT} || die_ret "Could create directory"
        mount ${LOOP_DEV} ${TMP_CHROOT_DIR}${MOUNT_POINT} || die_ret "Couldn't mount mountpoint"
    done
    return 0
}

function debootstap_download_packages_try_harder {
    local attempt=0
    local max_attempts=$MAX_DOWNLOAD_ATTEMPTS

    while true; do
        if [ $attempt -ge $max_attempts ]; then
            return 1
        fi
        debootstrap --download-only --verbose $DEBOOTSTRAP_PARAMS $BASE_MIRROR_URL
        if [ $? -ne 0 ]; then
            sleep 1
            attempt=$((attempt+1))
        else
            return 0
        fi
    done
}

function suppress_udev_start {
    # inhibit service startup in the chroot
    # do this *before* running deboostrap to suppress udev start
    # (by its postinst script)
    mkdir -p ${TMP_CHROOT_DIR}/usr/sbin
    cat > policy-rc.d << EOF
#!/bin/sh
# prevent any service from being started
exit 101
EOF
    chmod 755 policy-rc.d
    cp policy-rc.d ${TMP_CHROOT_DIR}/usr/sbin
}

function install_base_system {
    debootstap_download_packages_try_harder || die_ret "Couldn't retreive packages for debootstrap"

    #FIXME(agordeev): deboostrap will fetch mirror info despite the fact
    # that all needed packages were downloaded earlier
    debootstrap $DEBOOTSTRAP_PARAMS $BASE_MIRROR_URL || die_ret "Couldn't finish debootstrap successfully"
}

function apt_get_download_try_harder {
    local attempt=0
    local max_attempts=$MAX_DOWNLOAD_ATTEMPTS

    while true; do
        if [ $attempt -ge $max_attempts ]; then
            return 1
        fi
        chroot ${TMP_CHROOT_DIR} \
            env DEBIAN_FRONTEND=noninteractive \
            DEBCONF_NONINTERACTIVE_SEEN=true \
            LC_ALL=C LANG=C LANGUAGE=C \
            apt-get -y -d install ${INSTALL_PACKAGES}
        if [ $? -ne 0 ]; then
            sleep 1
            attempt=$((attempt+1))
        else
            return 0
        fi
    done
}

function setup_apt_mirrors {
    rm -f ${TMP_CHROOT_DIR}/etc/apt/sources.list
    rm -f ${TMP_CHROOT_DIR}/etc/apt/preferences
    IFS=','
    set -- $UBUNTU_MIRRORS
    unset IFS
    for ent; do
        # expecting 'suite|section|priority|uri'
        IFS='|'
        set -- $ent
        unset IFS
        local suite="$1"
        local section="$2"
        local priority="$3"
        shift; shift; shift
        local uri="$@"
        if [ -n "$section" ]; then
            echo "deb ${uri} ${suite} ${section}" >> "${TMP_CHROOT_DIR}/etc/apt/sources.list"
            if [ "$priority" != "None" ]; then
                for sec in $section; do
                    cat >> ${TMP_CHROOT_DIR}/etc/apt/preferences <<-EOF
Package: *
Pin: release a=${suite},c=${sec}
Pin-Priority: ${priority}

EOF
                done
            fi
        else
            echo "deb ${uri} ${suite}" >> "${TMP_CHROOT_DIR}/etc/apt/sources.list"
            if [ "$priority" != "None" ]; then
                cat >> ${TMP_CHROOT_DIR}/etc/apt/preferences <<-EOF
Package: *
Pin: release a=${suite}
Pin-Priority: ${priority}

EOF
            fi
        fi
    done
    return 0
}

function install_by_apt {
    echo 'APT::Get::AllowUnauthenticated 1;' | tee ${TMP_CHROOT_DIR}/etc/apt/apt.conf.d/02mirantis-unauthenticated

    setup_apt_mirrors || die_ret "Couldn't set up ubuntu mirrors"

    #FIXME:do retry for apt-get update?
    chroot ${TMP_CHROOT_DIR} apt-get update || die_ret "Couldn't update packages list from sources"
    if ! mountpoint -q ${TMP_CHROOT_DIR}/proc; then
        mount -t proc proc ${TMP_CHROOT_DIR}/proc
    fi
    apt_get_download_try_harder || die_ret "Couldn't retreive packages for apt-get install"

    chroot ${TMP_CHROOT_DIR} \
        env DEBIAN_FRONTEND=noninteractive \
        DEBCONF_NONINTERACTIVE_SEEN=true \
        LC_ALL=C LANG=C LANGUAGE=C \
        apt-get -y install ${INSTALL_PACKAGES} || die_ret "Couldn't install the rest of packages successfully"
}

function do_post_inst {
    #inject hardcoded root password `r00tme`
    sed -i 's%root:[\*,\!]%root:$6$IInX3Cqo$5xytL1VZbZTusOewFnG6couuF0Ia61yS3rbC6P5YbZP2TYclwHqMq9e3Tg8rvQxhxSlBXP1DZhdUamxdOBXK0.%' ${TMP_CHROOT_DIR}/etc/shadow

    #cloud-init reconfigure to use NoCloud data source
    echo "cloud-init cloud-init/datasources multiselect NoCloud, None" | chroot ${TMP_CHROOT_DIR} debconf-set-selections -v
    chroot ${TMP_CHROOT_DIR} dpkg-reconfigure -f noninteractive cloud-init

    # re-enable services
    rm -f ${TMP_CHROOT_DIR}/usr/sbin/policy-rc.d
    # clean apt settings
    rm -f ${TMP_CHROOT_DIR}/etc/apt/sources.list
    rm -f ${TMP_CHROOT_DIR}/etc/apt/preferences
}

# kill any stray process in chroot (just in a case some sloppy postinst
# script still hanging around)
signal_chrooted_processes() {
    local chroot_dir="$1"
    local signal="$2"
    local proc_root
    for p in `fuser -v "$chroot_dir" 2>/dev/null`; do
        proc_root="`readlink -f /proc/$p/root || true`"
        if [ "$proc_root" = "$chroot_dir" ]; then
            kill -s "$signal" $p
        fi
    done
}

function clean_chroot {
    signal_chrooted_processes $TMP_CHROOT_DIR TERM
    sleep 1
    signal_chrooted_processes $TMP_CHROOT_DIR KILL

    if mountpoint -q ${TMP_CHROOT_DIR}/proc; then
        umount -l ${TMP_CHROOT_DIR}/proc || true
    fi

}

umount_try_harder () {
    local abs_mount_point="$1"
    local umount_attempt=0
    local max_umount_attempts=10

    while mountpoint -q "$abs_mount_point" && ! umount "$abs_mount_point"; do
        if [ $umount_attempt -ge $max_umount_attempts ]; then
            return 1
        fi
        signal_chrooted_processes "$abs_mount_point" KILL
        sleep 1
        umount_attempt=$((umount_attempt+1))
    done
    return 0
}

function umount_resize_images {
    for idx in $(seq $((${#MOUNTPOINTS[@]} - 1)) -1 0); do
        MOUNT_POINT=${MOUNTPOINTS[$idx]}
        if [ "$MOUNT_POINT" == "/" ]; then
            MOUNT_POINT=""
        fi
        IMG_FILE_NAME=${TMP_BUILD_IMG_DIR}/${IMG_PREFIX}_${IMG_SUFFIX}$(echo $MOUNT_POINT | tr '/' '-').${IMG_ENDING}
        MOUNT_POINT=${MOUNTPOINTS[$idx]}
        SPARSE_FILE_NAME=${IMG_FILE_NAME}.${SPARSE_IMG_FILE_SUFFIX}
        LOOP_DEV=${LOOP_DEVICES_LIST[$idx]}
        FS_TYPE=${MOUNT_DICT[$MOUNT_POINT]}
        FINAL_IMAGE_NAME=${IMAGES_NAMES_DICT[$MOUNT_POINT]}
        if ! umount_try_harder "${TMP_CHROOT_DIR}${MOUNT_POINT}"; then
            umount -l "${TMP_CHROOT_DIR}${MOUNT_POINT}" || die_ret "Failed to umount $LOOP_DEV (${TMP_CHROOT_DIR}${MOUNT_POINT})"
        fi

        if [ "$FS_TYPE" == "ext2" ] || [ "$FS_TYPE" == "ext3" ] || [ "$FS_TYPE" == "ext4" ]; then
            e2fsck -yf ${LOOP_DEV} || die_ret "Couldn't check filesystem"
            resize2fs -F -M ${LOOP_DEV} || die_ret "Couldn't resize filesystem"
            # calculate fs size precisely
            BLOCK_COUNT=$(dumpe2fs -h ${LOOP_DEV} | grep 'Block count' | awk '{print $3}')
            BLOCK_SIZE=$(dumpe2fs -h ${LOOP_DEV} | grep 'Block size' | awk '{print $3}')
            BLOCK_K_SIZE=$(( $BLOCK_SIZE / 1024 ))
            BLOCK_K_COUNT=$(( 1 + $BLOCK_COUNT / 1024 ))
            EXPECTED_M_SIZE=$(( $BLOCK_K_COUNT * $BLOCK_K_SIZE ))
            dd if=${LOOP_DEV} of=${IMG_FILE_NAME} bs=1M count=${EXPECTED_M_SIZE} || die_ret "Couldn't copy image"
        else
            echo "Unsupported fs type $FS_TYPE. Exitting now!"
            exit 1
        fi
        chmod a+r ${IMG_FILE_NAME} || die_ret "Couldn't grant reading access to image file"
        gzip -f ${IMG_FILE_NAME}
        mv ${IMG_FILE_NAME}.gz ${DST_DIR}/${FINAL_IMAGE_NAME}
        rm -f ${SPARSE_FILE_NAME} || die_ret "Couldn't remove sparse image file"
    done
}

cleanup || die "Couldn't perform cleanup"

function build_images {
    make_dirs || return 1
    precreate_loop_devices || return 1
    create_loop_device_and_makefs || return 1
    do_mounts || return 1
    suppress_udev_start || return 1
    install_base_system || return 1
    #FIXME(agordeev): policy-rc.d will disappear after bootstrap exits
    suppress_udev_start || return 1
    install_by_apt || return 1
    do_post_inst || return 1
    clean_chroot || return 1
    umount_resize_images || return 1
}

build_images
if [ $? -ne 0 ]; then
    echo 'Building of images failed'
    cleanup || die_ret "Couldn't perform cleanup"
    exit 1
else
    echo 'Building of images finished successfuly'
    cleanup || die_ret "Couldn't perform cleanup"
    exit 0
fi
