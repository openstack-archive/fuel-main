#!/bin/bash

set -x

[ X`whoami` = X'root' ] || { echo "You must be root."; exit 1; }

SCRIPT_BASE_DIR=`dirname $0`
BASE_DIR=/var/lib/ci_libvirt/domains

CONFIG_DIR=$1
[ -z ${CONFIG_DIR} ] && { echo "CONFIG_FILE not set."; exit 1; }

. ${CONFIG_DIR}/domain.conf

[ -z ${DOMAIN_NAME} ] && { echo "DOMAIN_NAME not set."; exit 1; } 


echo "Checking if disk has qcow2 format. At the moment it is only supported format."
qemu-img info ${BASE_DIR}/${DOMAIN_NAME}/disk.qcow2 | grep "^file format" | grep -q qcow2 || { echo "Disk must have qcow2 format"; exit 1; }

echo "Connecting to nbd device ..."
modprobe nbd max_part=63
qemu-nbd -c /dev/nbd0 ${BASE_DIR}/${DOMAIN_NAME}/disk.qcow2 || { echo "Error occured while connecting disk to nbd device"; exit 1; }

echo "Mounting nbd into loop dir ..."
LOOP_DIR=`mktemp -d`
mount /dev/nbd0p1 ${LOOP_DIR}


echo "Injecting cookbooks ..."
cp -r ${CONFIG_DIR}/cookbooks ${LOOP_DIR}/root

echo "Injecting scripts ..."
cp -r ${CONFIG_DIR}/scripts ${LOOP_DIR}/root

echo "Adding command into rc.local to lauch chef-solo just after booting ..."
cat > ${LOOP_DIR}/etc/rc.local <<EOF
#!/bin/sh -e

flock -w 0 /var/lock/chef-solo.lock /usr/bin/chef-solo -l debug -c /root/scripts/solo.rb -j /root/scripts/solo.json || true

exit 0
EOF

echo "Unmounting loop dir ..."
umount ${LOOP_DIR} 


echo "Disconnecting nbd device ..."
qemu-nbd -d /dev/nbd0


