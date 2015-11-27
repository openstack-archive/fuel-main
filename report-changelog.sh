#!/bin/bash -e
PPC_CHANGELOG=${LOCAL_MIRROR}/ppc-packages.changelog

[ -f ${PPC_CHANGELOG} ] && rm ${PPC_CHANGELOG}
for packagename in `find ${LOCAL_MIRROR} -name \*.rpm | sort -u`; do
  echo ${packagename##*/} >> ${PPC_CHANGELOG}
  rpm -qp --changelog ${packagename} 2>/dev/null | sed -e '/^$/,$d' >> ${PPC_CHANGELOG}
  echo '' >> ${CENTOS_CHANGELOG}
done

