#!/bin/bash

set -x

[ X`whoami` = X'root' ] || { echo "You must be root."; exit 1; }

SCRIPT_BASE_DIR=`dirname $0`
BASE_DIR=/var/lib/ci_libvirt/domains

CONFIG_FILE=$1
[ -z ${CONFIG_FILE} ] && { echo "CONFIG_FILE not set."; exit 1; }

. ${CONFIG_FILE}

[ -z ${DOMAIN_NAME} ] && { echo "DOMAIN_NAME not set."; exit 1; } 
[ -z ${PURGE_AFTER_DESTROY} ] && PURGE_AFTER_DESTROY=false 

echo "Destroying domain ..."
virsh destroy ${DOMAIN_NAME}

if [ X${PURGE_AFTER_DESTROY} = Xtrue ]; then
    echo "Purging domain ..."
    rm -rf ${BASE_DIR}/${DOMAIN_NAME}
fi

