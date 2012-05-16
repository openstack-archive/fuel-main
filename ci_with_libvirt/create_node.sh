#!/bin/bash

set -x

[ X`whoami` = X'root' ] || { echo "You must be root."; exit 1; }

genmac(){
    local prefix=$1
    [[ -z $prefix ]] && prefix="52:54:00:00"
    echo $prefix`dd if=/dev/urandom count=1 2>/dev/null | md5sum | sed 's/^\(..\)\(..\).*$/\1:\2/'`
}

SCRIPT_BASE_DIR=`dirname $0`
BASE_DIR=/var/lib/ci_libvirt/domains

CONFIG_DIR=$1
[ -z ${CONFIG_DIR} ] && { echo "CONFIG_DIR not set."; exit 1; }

. ${CONFIG_DIR}/domain.conf

[ -z ${DOMAIN_NAME} ] && { echo "DOMAIN_NAME not set."; exit 1; } 
[ -z ${DOMAIN_MEMORY} ] && DOMAIN_MEMORY=1048576
[ -z ${DOMAIN_BRIDGE0} ] && { echo "DOMAIN_BRIDGE0 not set"; exit 1; }
[ -z ${DOMAIN_BRIDGE1} ] && { echo "DOMAIN_BRIDGE1 not set"; exit 1; }
[ -z ${DOMAIN_MAC0} ] && DOMAIN_MAC0=`genmac 52:54:00:00:`
[ -z ${DOMAIN_MAC1} ] && DOMAIN_MAC1=`genmac 52:54:00:01:`


echo "Creating domain base directory ..."
mkdir -p ${BASE_DIR}/${DOMAIN_NAME}

if [ -z ${DOMAIN_BASE_DISK} ]; then
    echo "Creating domain disk ..."
    kvm-img create -f qcow2 ${BASE_DIR}/${DOMAIN_NAME}/disk.qcow2 32G
else
    # if ${DOMAIN_BASE_DISK} begins with http we will try to download it
    # ${DOMAIN_BASE_DISK} must have bootloader on it
    if ( echo ${DOMAIN_BASE_DISK} | grep -q "^http" ); then
	wget -qO - ${DOMAIN_BASE_DISK} > ${BASE_DIR}/${DOMAIN_NAME}/disk.qcow2
    else
	cp ${DOMAIN_BASE_DISK} ${BASE_DIR}/${DOMAIN_NAME}/disk.qcow2
    fi
fi


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






