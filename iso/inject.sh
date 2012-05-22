#!/bin/bash

set -x
set -e

[ -z ${BUILDDIR} ] && BUILDDIR=/var/tmp/build_iso
[ -z ${REPODIR} ] && REPODIR=`dirname $0`/.. 

SCRIPTDIR=`dirname $0`

echo "Injecting cookbooks ..."
cp -r ${REPODIR}/cookbooks ${BUILDDIR} 

echo "Injecting scripts ..."
cp -r ${REPODIR}/scripts ${BUILDDIR}



exit 0


