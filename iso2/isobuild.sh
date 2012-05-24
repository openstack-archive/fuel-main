#!/bin/bash

set -x
set -e

[ X`whoami` = X'root' ] || { echo "You must be root to run this script."; exit 1; }



###########################
# VARIABLES
###########################
STAMP=`date +%Y%m%d%H%M%S`

SCRIPT=`readlink -f "$0"`
SCRIPTDIR=`dirname ${SCRIPT}`
REPO=${SCRIPTDIR}/..
GNUPG=${REPO}/gnupg
STAGE=${SCRIPTDIR}/stage

RELEASE=precise
VERSION=12.04

ORIGISO=/var/tmp/ubuntu-12.04-server-amd64.iso
NEWISONAME=nailgun-ubuntu-${VERSION}-amd64
[ -z ${NEWISODIR} ] && NEWISODIR=/var/tmp

MIRROR="http://ru.archive.ubuntu.com/ubuntu"
REQDEB=`cat ${REPO}/requirements-deb.txt | grep -v "^\s*$" | grep -v "^\s*#"`

BASEDIR=/var/tmp/build_iso2

ORIG=${BASEDIR}/orig
NEW=${BASEDIR}/new
EXTRAS=${BASEDIR}/extras
APTFTP=${BASEDIR}/aptftp
KEYRING=${BASEDIR}/keyring

TMPGNUPG=${BASEDIR}/gnupg
GPGKEYID=F8AF89DD
GPGKEYNAME="Mirantis Product"
GPGKEYEMAIL="<product@mirantis.com>"
GPGKEY="${GPGKEYNAME} ${GPGKEYEMAIL}"
GPGKEYPHRASE="naMu7aej"



###########################
# CLEANING
###########################
echo "Cleaning ..."
if (mount | grep -q ${ORIG}); then
    echo "Umounting ${ORIG} ..."
    umount ${ORIG}
fi

# echo "Removing ${BASEDIR} ..."
# rm -rf ${BASEDIR}

echo "Removing ${ORIG} ..."
rm -rf ${ORIG}

echo "Removing ${NEW} ..."
rm -rf ${NEW}

# echo "Removing ${EXTRAS} ..."
# rm -rf ${EXTRAS}

echo "Removing ${TMPGNUPG} ..."
rm -rf ${TMPGNUPG}

echo "Removing ${APTFTP} ..."
rm -rf ${APTFTP}

echo "Removing ${KEYRING} ..."
rm -rf ${KEYRING}





###########################
# STAGING
###########################

gmkdir -p ${ORIG}
mkdir -p ${NEW}

echo "Mounting original iso image ..."
mount | grep -q ${ORIG} && umount ${ORIG}
mount -o loop ${ORIGISO} ${ORIG}

echo "Syncing original iso to new iso ..."
rsync -a ${ORIG}/ ${NEW}
chmod -R u+w ${NEW}

echo "Syncing stage directory to new iso ..."
rsync -a ${STAGE}/ ${NEW}


###########################
# DOWNLOADING REQUIRED DEBS
###########################
mkdir -p ${EXTRAS}/state
touch ${EXTRAS}/state/status

mkdir -p ${EXTRAS}/archives
mkdir -p ${EXTRAS}/cache


mkdir -p ${EXTRAS}/etc/preferences.d
mkdir -p ${EXTRAS}/etc/apt.conf.d
echo "deb ${MIRROR} precise main restricted universe multiverse" > ${EXTRAS}/etc/sources.list
echo "deb-src ${MIRROR} precise main restricted universe multiverse" >> ${EXTRAS}/etc/sources.list


# possible apt configs
# Install-Recommends "true";
# Install-Suggests "true";


cat > ${EXTRAS}/etc/apt.conf <<EOF
APT
{
  Architecture "amd64";
  Default-Release "${RELEASE}";
  Get::AllowUnauthenticated "true";
};

Dir
{
  State "${EXTRAS}/state";
  State::status "status";
  
  Cache::archives "${EXTRAS}/archives";
  Cache "${EXTRAS}/cache";
  
  Etc "${EXTRAS}/etc";
};
EOF

apt-get -c=${EXTRAS}/etc/apt.conf update
for package in ${REQDEB}; do
    apt-get -c=${EXTRAS}/etc/apt.conf -d -y install ${package}
done

mkdir -p ${NEW}/pool/extras
cd ${EXTRAS}/archives
find -name "*.deb" -exec cp {} ${NEW}/pool/extras \;


# FIXME
# move this actions to chef
# debian-installer is very sensitive to chages in cdrom repository

# ###########################
# # REBUILDING KEYRING
# ###########################
# mkdir -p ${KEYRING}
# cp -rp ${GNUPG} ${TMPGNUPG}
# chmod 700 ${TMPGNUPG}
# chmod 600 ${TMPGNUPG}/*

# cd ${KEYRING}
# apt-get -c=${EXTRAS}/etc/apt.conf source ubuntu-keyring
# KEYRING_PACKAGE=`find -maxdepth 1 -name "ubuntu-keyring*" -type d -print`
# if [ -z ${KEYRING_PACKAGE} ]; then
#     echo "Cannot grab keyring source! Exiting."
#     exit 1
# fi

# cd ${KEYRING}/${KEYRING_PACKAGE}/keyrings
# GNUPGHOME=${TMPGNUPG} gpg --import < ubuntu-archive-keyring.gpg
# rm -f ubuntu-archive-keyring.gpg
# GNUPGHOME=${TMPGNUPG} gpg --export --output ubuntu-archive-keyring.gpg FBB75451 437D05B5 ${GPGKEYID}
# cd ${KEYRING}/${KEYRING_PACKAGE}
# dpkg-buildpackage -rfakeroot -m"${GPGKEY}" -k"${GPGKEYID}" -uc -us
# rm -f ${NEW}/pool/main/u/ubuntu-keyring/*
# cp ${KEYRING}/ubuntu-keyring*deb ${NEW}/pool/main/u/ubuntu-keyring/


# ###########################
# # UPDATING REPO
# ###########################
# mkdir -p ${APTFTP}/conf.d
# mkdir -p ${APTFTP}/indices
# mkdir -p ${APTFTP}/cache

# ARCHITECTURES="i386 amd64"
# SECTIONS="main restricted extras"

# for s in ${SECTIONS}; do
#     for a in ${ARCHITECTURES}; do
# 	mkdir -p ${NEW}/dists/${RELEASE}/${s}/binary-${a}
# 	cat > ${NEW}/dists/${RELEASE}/${s}/binary-${a}/Release <<EOF
# Archive: ${RELEASE}
# Version: ${VERSION}
# Component: ${s}
# Origin: Mirantis
# Label: Mirantis
# Architecture: ${a}
# EOF
#     done
#     mkdir -p ${NEW}/dists/${RELEASE}/${s}/debian-installer/binary-amd64
# done

# for suffix in \
#     extra.main \
#     main \
#     main.debian-installer \
#     restricted \
#     restricted.debian-installer; do
    
#     wget -qO- ${MIRROR}/indices/override.${RELEASE}.${suffix} > \
# 	${APTFTP}/indices/override.${RELEASE}.${suffix}
# done


# cat > ${APTFTP}/conf.d/apt-ftparchive-deb.conf <<EOF
# Dir {
#   ArchiveDir "${NEW}";
#   CacheDir "${APTFTP}/cache";
#   OverrideDir "${APTFTP}/indices";
# };

# Tree "dists/${RELEASE}" {
#   Architectures "${ARCHITECTURES}";
#   Sections "${SECTIONS}";
#   BinOverride "override.${RELEASE}.\$(SECTION)";
#   ExtraOverride "override.${RELEASE}.extra.\$(SECTION)";
# };

# TreeDefault {
#   Directory "pool/\$(SECTION)";
#   Packages "\$(DIST)/\$(SECTION)/binary-\$(ARCH)/Packages";
#   Contents "\$(DIST)/Contents-\$(ARCH)";
# };

# Default {
#   Packages {
#     Extensions ".deb";
#     Compress ". gzip";
#   };
#   Contents {
#     Compress "gzip";
#   };
# };
# EOF



# cat > ${APTFTP}/conf.d/apt-ftparchive-udeb.conf <<EOF
# Dir {
#   ArchiveDir "${NEW}";
#   CacheDir "${APTFTP}/cache";
#   OverrideDir "${APTFTP}/indices";
# };

# Tree "dists/${RELEASE}" {
#   Architectures "amd64";
#   Sections "main restricted";
#   BinOverride "override.${RELEASE}.\$(SECTION).debian-installer";
# };

# TreeDefault {
#   Directory "pool/\$(SECTION)";
#   Packages "\$(DIST)/\$(SECTION)/debian-installer/binary-\$(ARCH)/Packages";
#   Contents "\$(DIST)/Contents-debian-installer-\$(ARCH)";
# };

# Default {
#   Packages {
#     Extensions ".udeb";
#     Compress ". gzip";
#   };
#   Contents {
#     Compress "gzip";
#   };
# };
# EOF


# cp ${SCRIPTDIR}/aptftp/extraoverride.pl ${APTFTP}/conf.d/extraoverride.pl
# gunzip -c ${NEW}/dists/${RELEASE}/main/binary-amd64/Packages.gz > \
#     ${NEW}/dists/${RELEASE}/main/binary-amd64/Packages

# ${APTFTP}/conf.d/extraoverride.pl \
#     ${NEW}/dists/${RELEASE}/main/binary-amd64/Packages >> \
#     ${APTFTP}/indices/override.${RELEASE}.extra.main

# apt-ftparchive generate ${APTFTP}/conf.d/apt-ftparchive-deb.conf
# apt-ftparchive generate ${APTFTP}/conf.d/apt-ftparchive-udeb.conf

# cat > ${APTFTP}/conf.d/release.conf <<EOF
# APT::FTPArchive::Release::Origin "Mirantis";
# APT::FTPArchive::Release::Label "Mirantis";
# APT::FTPArchive::Release::Suite "${RELEASE}";
# APT::FTPArchive::Release::Version "${VERSION}";
# APT::FTPArchive::Release::Codename "${RELEASE}";
# APT::FTPArchive::Release::Architectures "${ARCHITECTURES}";
# APT::FTPArchive::Release::Components "${SECTIONS}";
# APT::FTPArchive::Release::Description "Mirantis Nailgun Repo";
# EOF

# apt-ftparchive -c ${APTFTP}/conf.d/release.conf release ${NEW}/dists/${RELEASE} > ${NEW}/dists/${RELEASE}/Release

# GNUPGHOME=${TMPGNUPG} gpg --yes --passphrase-file ${TMPGNUPG}/keyphrase --output ${NEW}/dists/${RELEASE}/Release.gpg -ba ${NEW}/dists/${RELEASE}/Release


###########################
# INJECT EXTRA FILES
###########################
mkdir -p ${NEW}/inject
cp -r ${REPO}/cookbooks ${NEW}/inject
cp -r ${REPO}/scripts ${NEW}/inject



###########################
# MAKE NEW ISO
###########################
echo "Calculating md5sums ..."
rm ${NEW}/md5sum.txt
(
    cd ${NEW}/ && \
    find . -type f -print0 | \
    xargs -0 md5sum | \
    grep -v "boot.cat" | \
    grep -v "md5sum.txt" > md5sum.txt
)


echo "Building iso image ..."
mkisofs -r -V "Mirantis Nailgun" \
    -cache-inodes \
    -J -l -b isolinux/isolinux.bin \
    -c isolinux/boot.cat -no-emul-boot \
    -boot-load-size 4 -boot-info-table \
    -o ${NEWISODIR}/${NEWISONAME}.${STAMP}.iso ${NEW}/


rm -f ${NEWISODIR}/${NEWISONAME}.last.iso
(
    cd ${NEWISODIR}
    ln -s ${NEWISONAME}.${STAMP}.iso ${NEWISONAME}.last.iso
)
