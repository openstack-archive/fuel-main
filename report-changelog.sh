#!/bin/bash -e
MIRROR_DIR=${LOCAL_MIRROR}
CENTOS_MIRROR_DIR=${LOCAL_MIRROR_CENTOS_OS_BASE_URL}
UBUNTU_MIRROR_DIR=${LOCAL_MIRROR_UBUNTU}
CENTOS_CHANGELOG=${MIRROR_DIR}/centos-packages.changelog
UBUNTU_CHANGELOG=${MIRROR_DIR}/ubuntu-packages.changelog

[ -f ${CENTOS_CHANGELOG} ] && rm ${CENTOS_CHANGELOG}
for packagename in `find ${CENTOS_MIRROR_DIR} -name \*.rpm`; do
  echo ${packagename##*/} >> ${CENTOS_CHANGELOG}
  rpm -qp --changelog ${packagename} 2>/dev/null | sed -e '/^$/,$d' >> ${CENTOS_CHANGELOG}
  echo '' >> ${CENTOS_CHANGELOG}
done

[ -f ${UBUNTU_CHANGELOG} ] && rm ${UBUNTU_CHANGELOG}
for packagename in `find ${UBUNTU_MIRROR_DIR} -name \*.deb`; do
    pkgname=${packagename##*/}
    DATAFILE=`ar t $packagename | grep ^data`
    case ${DATAFILE##*.} in
        bz2) BZFLAG='--bzip2' ;;
         gz) BZFLAG='-z' ;;
         xz) BZFLAG='-J' ;;
          *) echo error "$packagename" ; exit 0 ;;
    esac
    CHANGELOGFILE=`ar p $packagename $DATAFILE | tar $BZFLAG -tvf - | grep '/usr/share/doc/' | grep "/changelog\.Debian\.gz" || :`
    CHANGELOGFILE=${CHANGELOGFILE##* }
    if [[ ${CHANGELOGFILE:0:2} == './' ]]; then
        ar p $packagename $DATAFILE | tar $BZFLAG -xO $CHANGELOGFILE | gunzip | sed '/^/,/--/!d;/--/q' >> ${UBUNTU_CHANGELOG}
        echo '' >> ${UBUNTU_CHANGELOG}
    fi
done
