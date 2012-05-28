#!/bin/bash

#set -x
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
cat > ${EXTRAS}/etc/sources.list <<EOF
deb ${MIRROR} precise main restricted universe multiverse
deb-src ${MIRROR} precise main restricted universe multiverse
deb http://apt.opscode.com ${RELEASE}-0.10 main
EOF

cat > ${EXTRAS}/etc/preferences.d/opscode <<EOF
Package: *
Pin: origin "apt.opscode.com"
Pin-Priority: 999
EOF


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

Debug::NoLocking "true";
EOF

apt-get -c=${EXTRAS}/etc/apt.conf update
for package in ${REQDEB}; do
    apt-get -c=${EXTRAS}/etc/apt.conf -d -y install ${package}
done

(
    cd ${EXTRAS}/archives

    find -name "*.deb" -o -name "*.udeb" | while read debfile; do
	pack=`basename ${debfile} | awk -F_ '{print $1}'`
	if (echo ${packname} | grep -q "^lib"); then
	    directory=lib`echo ${packname} | cut -c4`/${packname}
	else
	    directory=`echo ${packname} | cut -c1`/${packname}
	fi
	
	mkdir -p ${NEW}/pool/${directory}
	cp ${debfile} ${NEW}/pool/${directory}
    done
)


# FIXME
# move this actions to chef
# debian-installer is very sensitive to chages in cdrom repository

###########################
# REBUILDING KEYRING
###########################
mkdir -p ${KEYRING}
cp -rp ${GNUPG} ${TMPGNUPG}
chown -R root:root ${TMPGNUPG}
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
mkdir -p ${APTFTP}/cache

ARCHITECTURES="i386 amd64"
SECTIONS="main restricted universe multiverse"

for s in ${SECTIONS}; do
    for a in ${ARCHITECTURES}; do
	mkdir -p ${NEW}/dists/${RELEASE}/${s}/binary-${a}
	cat > ${NEW}/dists/${RELEASE}/${s}/binary-${a}/Release <<EOF
Archive: ${RELEASE}
Version: ${VERSION}
Component: ${s}
Origin: Mirantis
Label: Mirantis
Architecture: ${a}
EOF
    done
    mkdir -p ${NEW}/dists/${RELEASE}/${s}/debian-installer/binary-amd64
done

# for suffix in \
#     extra.main \
#     main \
#     main.debian-installer \
#     restricted \
#     restricted.debian-installer; do
    
#     wget -qO- ${MIRROR}/indices/override.${RELEASE}.${suffix} > \
# 	${APTFTP}/indices/override.${RELEASE}.${suffix}
# done

echo "Downloading indices ..."
for s in ${SECTIONS}; do
    wget -qO- ${MIRROR}/indices/override.${RELEASE}.${s}.debian-installer > \
	${APTFTP}/indices/override.${RELEASE}.${s}.debian-installer
    
    wget -qO- ${MIRROR}/indices/override.${RELEASE}.${s} > \
	${APTFTP}/indices/override.${RELEASE}.${s}
    
    wget -qO- ${MIRROR}/indices/override.${RELEASE}.extra.${s} > \
	${APTFTP}/indices/override.${RELEASE}.extra.${s}
done

gunzip -c ${NEW}/dists/${RELEASE}/main/binary-amd64/Packages.gz | \
    ${SCRIPTDIR}/aptftp/extraoverride.pl >> \
    ${APTFTP}/indices/override.${RELEASE}.extra.main

for s in ${SECTIONS}; do
    for a in ${ARCHITECTURES}; do

	[ -r ${APTFTP}/indices/override.${RELEASE}.${s} ] && \
	    override=${APTFTP}/indices/override.${RELEASE}.${s} || \
	    unset override
	[ -r ${APTFTP}/indices/override.${RELEASE}.extra.${s} ] && \
	    extraoverride="-e ${APTFTP}/indices/override.${RELEASE}.extra.${s}" || \
	    unset extraoverride

	echo ">>> DEB"
	echo ">>> section: ${s}"
	echo ">>> arch: ${a}"
	echo ">>> override: ${override}"
	echo ">>> extraoverride: ${extraoverride}"


	if [ -d ${NEW}/pool/${s} ]; then


	    (
		cd ${NEW} && dpkg-scanpackages -a ${a} -tdeb ${extraoverride} \
		    pool/${s} \
		    ${override} > \
		    ${NEW}/dists/${RELEASE}/${s}/binary-${a}/Packages
	    )
	else
	    echo -n > ${NEW}/dists/${RELEASE}/${s}/binary-${a}/Packages
	fi
	gzip -c ${NEW}/dists/${RELEASE}/${s}/binary-${a}/Packages > \
	    ${NEW}/dists/${RELEASE}/${s}/binary-${a}/Packages.gz
    done

    [ -r ${APTFTP}/indices/override.${RELEASE}.${s}.debian-installer ] && \
	override=${APTFTP}/indices/override.${RELEASE}.${s}.debian-installer || \
	unset override

    echo ">>> UDEB"
    echo ">>> section: ${s}"
    echo ">>> override: ${override}"

    if [ -d ${NEW}/pool/${s} ]; then
	
	echo ">>> ${NEW}/pool/${s} exists"
	
	(
	    cd ${NEW} && dpkg-scanpackages -a amd64 -tudeb \
		pool/${s} \
		${override} > \
		${NEW}/dists/${RELEASE}/${s}/debian-installer/binary-amd64/Packages
	)
    else
	echo -n > ${NEW}/dists/${RELEASE}/${s}/debian-installer/binary-amd64/Packages
    fi
    gzip -c ${NEW}/dists/${RELEASE}/${s}/debian-installer/binary-amd64/Packages > \
	${NEW}/dists/${RELEASE}/${s}/debian-installer/binary-amd64/Packages.gz
done

#!!!!! NEVER NEVER USE apt-ftparchive FOR SCANNING PACKAGES
#!!!!! IT IS BUGGGGGGGGGY

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

# apt-ftparchive generate ${APTFTP}/conf.d/apt-ftparchive-deb.conf
# apt-ftparchive generate ${APTFTP}/conf.d/apt-ftparchive-udeb.conf

echo "Creating main Release file in cdrom repo"

cat > ${APTFTP}/conf.d/release.conf <<EOF
APT::FTPArchive::Release::Origin "Mirantis";
APT::FTPArchive::Release::Label "Mirantis";
APT::FTPArchive::Release::Suite "${RELEASE}";
APT::FTPArchive::Release::Version "${VERSION}";
APT::FTPArchive::Release::Codename "${RELEASE}";
APT::FTPArchive::Release::Architectures "${ARCHITECTURES}";
APT::FTPArchive::Release::Components "${SECTIONS}";
APT::FTPArchive::Release::Description "Mirantis Nailgun Repo";
EOF


apt-ftparchive -c ${APTFTP}/conf.d/release.conf release ${NEW}/dists/${RELEASE} > ${NEW}/dists/${RELEASE}/Release


echo "Signing main Release file in cdrom repo ..."
GNUPGHOME=${TMPGNUPG} gpg --no-tty --default-key ${GPGKEYID} --yes --passphrase-file ${TMPGNUPG}/keyphrase --output ${NEW}/dists/${RELEASE}/Release.gpg -ba ${NEW}/dists/${RELEASE}/Release


###########################
# INJECT EXTRA FILES
###########################
echo "Injecting some files into iso ..."
mkdir -p ${NEW}/inject/scripts
cp -r ${APTFTP}/indices ${NEW}/inject
cp -r ${REPO}/cookbooks ${NEW}/inject
cp ${REPO}/scripts/solo-admin.json ${NEW}/inject/scripts/solo.json
cp ${REPO}/scripts/solo.rb ${NEW}/inject/scripts
cp ${REPO}/scripts/solo.cron ${NEW}/inject/scripts
cp ${REPO}/scripts/solo.rc.local ${NEW}/inject/scripts

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
