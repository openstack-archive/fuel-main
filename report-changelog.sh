#!/bin/bash -e
MIRROR_DIR=${LOCAL_MIRROR}
CENTOS_CHANGELOG=${MIRROR_DIR}/centos-packages.changelog
UBUNTU_CHANGELOG=${MIRROR_DIR}/ubuntu-packages.changelog
[ -f ${CENTOS_CHANGELOG} ] && rm ${CENTOS_CHANGELOG}
for packagename in `find ${MIRROR_DIR} -name \*.rpm | sort -u`; do
  echo ${packagename##*/} >> ${CENTOS_CHANGELOG}
  rpm -qp --changelog ${packagename} 2>/dev/null | sed -e '/^$/,$d' >> ${CENTOS_CHANGELOG}
  echo '' >> ${CENTOS_CHANGELOG}
done

[ -f ${UBUNTU_CHANGELOG} ] && rm ${UBUNTU_CHANGELOG}
for packagename in `find ${MIRROR_DIR} -name \*.deb | sort -u`; do
    pkgname=${packagename##*/}
    DATAFILE=`ar t $packagename | grep ^data`
    case ${DATAFILE##*.} in
        bz2) ZFLAG='--bzip2' ;;
         gz) ZFLAG='-z' ;;
         xz) ZFLAG='-J' ;;
          *) echo error "$packagename" ; exit 0 ;;
    esac
    CHANGELOGFILE=`ar p $packagename $DATAFILE | tar $ZFLAG -tvf - | grep '/usr/share/doc/' | grep "/changelog\.Debian\.gz" || :`
    CHANGELOGFILE=${CHANGELOGFILE##* }
    if [[ ${CHANGELOGFILE:0:2} == './' ]]; then
        ar p $packagename $DATAFILE | tar $ZFLAG -xO $CHANGELOGFILE | gzip -cd | sed -n '1,/--/ p' >> ${UBUNTU_CHANGELOG}
        echo '' >> ${UBUNTU_CHANGELOG}
    fi
done
