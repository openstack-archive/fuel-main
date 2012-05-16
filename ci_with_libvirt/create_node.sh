#!/bin/bash

set -x

[ X`whoami` = X'root' ] || { echo "You must be root."; exit 1; }

genmac(){
    prefix=$1
    [[ -z $prefix ]] && prefix="52:54:00:00"
    echo $prefix`dd if=/dev/urandom count=1 2>/dev/null | md5sum | sed 's/^\(..\)\(..\).*$/\1:\2/'`
}

SCRIPT_BASE_DIR=`dirname $0`
BASE_DIR=/var/lib/ci_libvirt/domains

CONFIG_FILE=$1
[ -z ${CONFIG_FILE} ] && { echo "CONFIG_FILE not set."; exit 1; }

. ${CONFIG_FILE}

[ -z ${DOMAIN_NAME} ] && { echo "DOMAIN_NAME not set."; exit 1; } 
[ -z ${DOMAIN_MEMORY} ] && DOMAIN_MEMORY=1048576
[ -z ${DOMAIN_BRIDGE0} ] && { echo "DOMAIN_BRIDGE0 not set"; exit 1; }
[ -z ${DOMAIN_BRIDGE1} ] && { echo "DOMAIN_BRIDGE1 not set"; exit 1; }
[ -z ${DOMAIN_MAC0} ] && DOMAIN_MAC0=`genmac 52:54:00:00:`
[ -z ${DOMAIN_MAC1} ] && DOMAIN_MAC1=`genmac 52:54:00:01:`


echo "Creating domain base directory ..."
mkdir -p ${BASE_DIR}/${DOMAIN_NAME}

echo "Creating domain disk ..."
kvm-img create -f qcow2 ${BASE_DIR}/${DOMAIN_NAME}/disk.qcow2 32G

# if you need to loop qcow2 file use qemu-nbd
# modprobe nbd max_part=63
# qemu-nbd -c /dev/nbd0 disk.qcow2

# if you need to make partitions on /dev/ndb0 use sfdisk

echo "Templating domain.xml"
sed -e "
s/\${domain_name}/${DOMAIN_NAME}/g
s/\${domain_memory}/${DOMAIN_MEMORY}/g
s#\${domain_disk}#${BASE_DIR}/${DOMAIN_NAME}/disk.qcow2#g
s/\${domain_mac0}/${DOMAIN_MAC0}/g
s/\${domain_mac1}/${DOMAIN_MAC1}/g
s/\${domain_bridge0}/${DOMAIN_BRIDGE0}/g
s/\${domain_bridge1}/${DOMAIN_BRIDGE1}/g
" ${SCRIPT_BASE_DIR}/domain.xml.template > ${BASE_DIR}/${DOMAIN_NAME}/domain.xml

echo "Defining domain ..."
virsh define ${BASE_DIR}/${DOMAIN_NAME}/domain.xml

echo "Starting domain ..."
virsh start ${DOMAIN_NAME}





