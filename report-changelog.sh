#!/bin/bash -e
CENTOS_CHANGELOG=${LOCAL_MIRROR}/centos-packages.changelog
[ -f ${CENTOS_CHANGELOG} ] && rm ${CENTOS_CHANGELOG}
for packagename in `find ${LOCAL_MIRROR} -name \*.rpm | sort -u`; do
  echo ${packagename##*/} >> ${CENTOS_CHANGELOG}
  rpm -qp --changelog ${packagename} 2>/dev/null | sed -e '/^$/,$d' >> ${CENTOS_CHANGELOG}
  echo '' >> ${CENTOS_CHANGELOG}
done
