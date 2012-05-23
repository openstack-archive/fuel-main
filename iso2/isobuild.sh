#!/bin/bash

set -x
set -e

[ X`whoami` = X'root' ] || { echo "You must be root to run this script."; exit 1; }



###########################
# VARIABLES
###########################

SCRIPT=`readlink -f "$0"`
SCRIPTDIR=`dirname ${SCRIPT}`
REPO=${SCRIPTDIR}/..
GNUPG=${REPO}/gnupg
STAGE=${SCRIPTDIR}/stage

RELEASE=precise
VERSION=12.04

ORIGISO=/var/tmp/ubuntu-12.04-server-amd64.iso
NEWISO=/var/tmp/mirantis-nailgun-ubuntu-12.04-amd64.iso
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
# echo "Cleaning ..."
# if (mount | grep -q ${ORIG}); then
#     echo "Umounting ${ORIG} ..."
#     umount ${ORIG}
# fi
# echo "Removing ${BASEDIR} ..."
# rm -rf ${BASEDIR}
# echo "Removing ${NEWISO}"
# rm -f ${NEWISO}




###########################
# STAGING
###########################
mkdir -p ${ORIG}
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


###########################
# REBUILDING KEYRING
###########################
mkdir -p ${KEYRING}
cp -rp ${GNUPG} ${TMPGNUPG}
chmod 700 ${TMPGNUPG}
chmod 600 ${TMPGNUPG}/*

cd ${KEYRING}
apt-get -c=${EXTRAS}/etc/apt.conf source ubuntu-keyring
KEYRING_PACKAGE=`find -maxdepth 1 -name "ubuntu-keyring*" -type d -print`
if [ -z ${KEYRING_PACKAGE} ]; then
    echo "Cannot grab keyring source! Exiting."
    exit 1
fi

cd ${KEYRING}/${KEYRING_PACKAGE}/keyrings
GNUPGHOME=${TMPGNUPG} gpg --import < ubuntu-archive-keyring.gpg
rm -f ubuntu-archive-keyring.gpg
GNUPGHOME=${TMPGNUPG} gpg --export --output ubuntu-archive-keyring.gpg FBB75451 437D05B5 ${GPGKEYID}
cd ${KEYRING}/${KEYRING_PACKAGE}
dpkg-buildpackage -rfakeroot -m"${GPGKEY}" -k"${GPGKEYID}" -uc -us
rm -f ${NEW}/pool/main/u/ubuntu-keyring/*
cp ${KEYRING}/ubuntu-keyring*deb ${NEW}/pool/main/u/ubuntu-keyring/


###########################
# UPDATING REPO
###########################
mkdir -p ${APTFTP}/conf.d
mkdir -p ${APTFTP}/indices

for suffix in \
    extra.main \
    main \
    main.debian-installer \
    restricted \
    restricted.debian-installer; do
    
    wget -qO- ${MIRROR}/indices/override.${RELEASE}.${suffix} > \
	${APTFTP}/indices/override.${RELEASE}.${suffix}
done

cat > ${APTFTP}/conf.d/release.conf <<EOF
APT::FTPArchive::Release::Codename: "${RELEASE}";
APT::FTPArchive::Release::Suite: "stable";
APT::FTPArchive::Release::Version: "${VERSION}";
APT::FTPArchive::Release::Components: "main restricted extras";
APT::FTPArchive::Release::Origin: "Mirantis";
APT::FTPArchive::Release::Label: "Mirantis";
APT::FTPArchive::Release::Architectures: "i386 amd64";
APT::FTPArchive::Release::Description "Mirantis Repo";
EOF


for arch in i386 amd64; do

    cat > ${APTFTP}/conf.d/apt-ftparchive-deb-${arch}.conf <<EOF
Dir {
  ArchiveDir "${NEW}";
};

Tree {
  Architectures "${arch}";
};

TreeDefault {
  Directory "pool/";
};

BinDirectory "pool/main" {
  Packages "dists/${RELEASE}/main/binary-${arch}/Packages";
  BinOverride "${APTFTP}/indices/override.${RELEASE}.main";
  ExtraOverride "${APTFTP}/indices/override.${RELEASE}.extra2.main";
};

BinDirectory "pool/restricted" {
  Packages "dists/${RELEASE}/restricted/binary-${arch}/Packages";
  BinOverride "${APTFTP}/indices/override.${RELEASE}.restricted";
};

Default {
  Packages {
    Extensions ".deb";
    Compress ". gzip";
  };
};

Contents {
  Compress "gzip";
};
EOF


    cat > ${APTFTP}/conf.d/apt-ftparchive-extras-${arch}.conf <<EOF
Dir {
  ArchiveDir "${NEW}";
};

TreeDefault {
  Directory "pool/";
};

BinDirectory "pool/extras" {
  Packages "dists/${RELEASE}/extras/binary-${arch}/Packages";
  BinOverride "${APTFTP}/indices/override.${RELEASE}.main";
};

Default {
  Packages {
    Extensions ".deb";
    Compress ". gzip";
  };
};

Contents {
  Compress "gzip";
};
EOF



done

cat > ${APTFTP}/conf.d/apt-ftparchive-udeb.conf <<EOF
Dir {
  ArchiveDir "${NEW}";
};

TreeDefault {
  Directory "pool/";
};

BinDirectory "pool/main" {
  Packages "dists/${RELEASE}/main/debian-installer/binary-amd64/Packages";
  BinOverride "${APTFTP}/indices/override.${RELEASE}.main.debian-installer";
};

BinDirectory "pool/restricted" {
  Packages "dists/${RELEASE}/restricted/debian-installer/binary-amd64/Packages";
  BinOverride "${APTFTP}/indices/override.${RELEASE}.restricted.debian-installer";
};

Default {
  Packages {
    Extensions ".deb";
    Compress ". gzip";
  };
};

Contents {
  Compress "gzip";
};
EOF





cp ${SCRIPTDIR}/aptftp/extraoverride.pl ${APTFTP}/conf.d/extraoverride.pl
gunzip -c ${NEW}/dists/${RELEASE}/main/binary-amd64/Packages.gz > \
    ${NEW}/dists/${RELEASE}/main/binary-amd64/Packages

${APTFTP}/conf.d/extraoverride.pl \
    ${NEW}/dists/${RELEASE}/main/binary-amd64/Packages > \
    ${APTFTP}/indices/override.${RELEASE}.extra2.main

apt-ftparchive --arch amd64 generate ${APTFTP}/conf.d/apt-ftparchive-deb-amd64.conf
apt-ftparchive --arch i386 generate ${APTFTP}/conf.d/apt-ftparchive-deb-i386.conf

mkdir -p ${NEW}/dists/${RELEASE}/extras/binary-amd64
mkdir -p ${NEW}/dists/${RELEASE}/extras/binary-i386
apt-ftparchive --arch amd64 generate ${APTFTP}/conf.d/apt-ftparchive-extras-amd64.conf
apt-ftparchive --arch i386 generate ${APTFTP}/conf.d/apt-ftparchive-extras-i386.conf


apt-ftparchive --arch amd64 generate ${APTFTP}/conf.d/apt-ftparchive-udeb.conf

apt-ftparchive -c ${APTFTP}/conf.d/release.conf release ${NEW}/dists/${RELEASE} > ${NEW}/dists/${RELEASE}/Release





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
    -o ${NEWISO} ${NEW}/


