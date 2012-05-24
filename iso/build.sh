#!/bin/bash

set -x
set -e

[ X`whoami` = X'root' ] || { echo "You must be root."; exit 1; }

[ -z ${BUILDDIR} ] && BUILDDIR=/var/tmp/build_iso
echo "BUILDDIR=${BUILDDIR}"
[ -z ${REPODIR} ] && REPODIR=`dirname $0`/.. 
echo "REPODIR=${REPODIR}"

SCRIPTDIR=`dirname $0`

[ -z ${ORIGISO} ] && ORIGISO=/var/tmp/ubuntu-12.04-server-amd64.iso
TEMPDIR=`mktemp -d`
[ -z ${ISO} ] && ISO=/var/tmp/mirantis-nailgun-ubuntu-12.04-amd64.iso


echo "Cleaning iso ..."
rm -rf ${BUILDDIR}
mkdir -p ${BUILDDIR}

echo "Copying orig iso into build dir ..."
mount -o loop ${ORIGISO} ${TEMPDIR} && \
rsync -a ${TEMPDIR}/ ${BUILDDIR} && chmod -R u+w ${BUILDDIR} && \
umount ${TEMPDIR}



echo "Editing install menu ..."
cat > ${BUILDDIR}/isolinux/txt.cfg <<EOF 
default install
label install
  menu label ^Mirantis Nailgun
  kernel /install/vmlinuz
  append  priority=critical locale=en_US file=/cdrom/preseed/mirantis-nailgun.seed vga=788 initrd=/install/initrd.gz quiet --
EOF

cat > ${BUILDDIR}/isolinux/menu.cfg <<EOF
menu hshift 13
menu width 49
menu margin 8

menu title Installer boot menu
include stdmenu.cfg
include txt.cfg
EOF

echo "Automating install process ..."
cat > ${BUILDDIR}/isolinux/lang <<EOF
en
EOF

cp ${REPODIR}/iso/mirantis-nailgun.seed ${BUILDDIR}/preseed

exit 0

echo "Creating repo ..."
BUILDDIR=${BUILDDIR} REPODIR=${REPODIR} ${SCRIPTDIR}/repo.sh

echo "Injecting files ..."
BUILDDIR=${BUILDDIR} REPODIR=${REPODIR} ${SCRIPTDIR}/inject.sh

echo "Calculating md5sums ..."
rm ${BUILDDIR}/md5sum.txt
(cd ${BUILDDIR}/ && find . -type f -print0 | xargs -0 md5sum | grep -v "boot.cat" | grep -v "md5sum.txt" > md5sum.txt)


echo "Building iso image ..."
mkisofs -r -V "Mirantis Nailgun" \
            -cache-inodes \
            -J -l -b isolinux/isolinux.bin \
            -c isolinux/boot.cat -no-emul-boot \
            -boot-load-size 4 -boot-info-table \
            -o ${ISO} ${BUILDDIR}/


