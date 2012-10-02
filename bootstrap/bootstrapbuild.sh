#!/bin/bash

#set -x
set -e

[ X`whoami` = X'root' ] || { echo "You must be root to run this script."; exit 1; }
[ -n "$BINARIES_DIR" ] || { echo "BINARIES_DIR variable should be defined."; exit 1; }
[ -n "$BASEDIR" ] || { echo "BASEDIR variable should be defined."; exit 1; }

BASEDIR=`readlink -f $BASEDIR`
BINARIES_DIR=`readlink -f $BINARIES_DIR`

###########################
# VARIABLES
###########################
STAMP=`date +%Y%m%d%H%M%S`

SCRIPT=`readlink -f "$0"`
SCRIPTDIR=`dirname "${SCRIPT}"`
REPO=${SCRIPTDIR}/..
SOLO=${SCRIPTDIR}/solo
SYNC=${SCRIPTDIR}/sync
SSH=${SCRIPTDIR}/ssh

GNUPG=${REPO}/gnupg

RELEASE=precise
VERSION=12.04

ORIGISO=${BINARIES_DIR}/ubuntu-12.04-server-amd64.iso
BOOTSTRAPNAME=""
BOOTSTRAPDIR=${BASEDIR}

INITRD=${BOOTSTRAPNAME}initrd
INITRDGZ=${INITRD}.gz
INITRD_SIZE=614400 #kilobytes
LINUX=${BOOTSTRAPNAME}linux

MIRROR="http://ru.archive.ubuntu.com/ubuntu"
REQDEB=`cat ${REPO}/requirements-deb.txt | grep -v "^\s*$" | grep -v "^\s*#"`

INITRD_FS=${BASEDIR}/initrd-fs
INITRD_LOOP=${BASEDIR}/initrd-loop
INITRD_MODULES=${BASEDIR}/modules

DEBOOTSTRAP_INCLUDE=less,vim,bash,net-tools,isc-dhcp-client,rsyslog,cron,iputils-ping,openssh-server,ruby-httpclient,ruby-json,ohai,rubygems\
,mcollective,python-scapy,vlan,tcpdump
DEBOOTSTRAP_EXCLUDE=

ORIG=${BASEDIR}/orig
NEW=${BASEDIR}/new
EXTRAS=${BASEDIR}/extras
KEYRING=${BASEDIR}/keyring
INDICES=${BASEDIR}/indices

TMPGNUPG=${BASEDIR}/gnupg
GPGKEYID=F8AF89DD
GPGKEYNAME="Mirantis Product"
GPGKEYEMAIL="<product@mirantis.com>"
GPGKEY="${GPGKEYNAME} ${GPGKEYEMAIL}"
GPGPASSWDFILE=${TMPGNUPG}/keyphrase

ARCHITECTURES="i386 amd64"
SECTIONS="main restricted universe multiverse"



###########################
# CLEANING
###########################
echo "Cleaning ..."
if (mount | grep -q ${ORIG}); then
    echo "Umounting ${ORIG} ..."
    umount ${ORIG}
fi

if (mount | grep -q ${INITRD_LOOP}); then
    echo "Umounting ${INITRD_LOOP} ..."
    umount ${INITRD_LOOP}
fi

# echo "Removing ${BASEDIR} ..."
# rm -rf ${BASEDIR}

echo "Removing ${ORIG} ..."
rm -rf ${ORIG}

echo "Removing ${INDICES} ..."
rm -rf ${INDICES}

# echo "Removing ${EXTRAS} ..."
# rm -rf ${EXTRAS}

echo "Removing ${TMPGNUPG} ..."
rm -rf ${TMPGNUPG}

echo "Removing ${KEYRING} ..."
rm -rf ${KEYRING}


###########################
# MOUNTING AND SYNCING ORIG ISO
###########################

mkdir -p ${ORIG}
mkdir -p ${NEW}

echo "Mounting original iso image ..."
mount -o loop ${ORIGISO} ${ORIG}

echo "Syncing original iso to new iso ..."
rsync -a ${ORIG}/ ${NEW}
chmod -R u+w ${NEW}


###########################
# DOWNLOADING INDICES
###########################
echo "Downloading indices ..."
mkdir -p ${INDICES}

for s in ${SECTIONS}; do
    wget -qO- ${MIRROR}/indices/override.${RELEASE}.${s}.debian-installer > \
	${INDICES}/override.${RELEASE}.${s}.debian-installer
    
    wget -qO- ${MIRROR}/indices/override.${RELEASE}.${s} > \
	${INDICES}/override.${RELEASE}.${s}
    
    wget -qO- ${MIRROR}/indices/override.${RELEASE}.extra.${s} > \
	${INDICES}/override.${RELEASE}.extra.${s}
done

###########################
# REORGANIZE POOL
###########################
echo "Reorganizing pool ..."
(
    cd ${NEW}/pool
    find -type f \( -name "*.deb" -o -name "*.udeb" \) | while read debfile; do
	    debbase=`basename ${debfile}`
	    packname=`echo ${debbase} | awk -F_ '{print $1}'`
	    section=`grep "^${packname}\s" ${INDICES}/* | \
		grep -v extra | head -1 | awk -F: '{print $1}' | \
		awk -F. '{print $3}'`
	    test -z ${section} && section=main
	    mkdir -p ${NEW}/pools/${RELEASE}/${section}
	    mv ${debfile} ${NEW}/pools/${RELEASE}/${section}
	done
)
rm -fr ${NEW}/pool


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

echo "Linking files that already in pool ..."
find ${NEW}/pools/${RELEASE} -name "*.deb" -o -name "*.udeb" | while read debfile; do
    debbase=`basename ${debfile}`
    ln -sf  ${debfile} ${EXTRAS}/archives/${debbase}
done

echo "Downloading requied packages ..."
apt-get -c=${EXTRAS}/etc/apt.conf update
for package in ${REQDEB}; do
    apt-get -c=${EXTRAS}/etc/apt.conf -d -y install ${package}
done

find ${EXTRAS}/archives -type f \( -name "*.deb" -o -name "*.udeb" \) | while read debfile; do
    debbase=`basename ${debfile}`
    packname=`echo ${debbase} | awk -F_ '{print $1}'`
    section=`grep "^${packname}\s" ${INDICES}/* | \
	grep -v extra | head -1 | awk -F: '{print $1}' | \
	awk -F. '{print $3}'`
    test -z ${section} && section=main
    mkdir -p ${NEW}/pools/${RELEASE}/${section}
    cp ${debfile} ${NEW}/pools/${RELEASE}/${section}
done


###########################
# REBUILDING KEYRING
###########################
echo "Rebuilding ubuntu-keyring packages ..."

mkdir -p ${KEYRING}

(
    cd ${KEYRING} && apt-get -c=${EXTRAS}/etc/apt.conf source ubuntu-keyring
)

KEYRING_PACKAGE=`find ${KEYRING} -maxdepth 1 \
    -name "ubuntu-keyring*" -type d -print | xargs basename`
if [ -z ${KEYRING_PACKAGE} ]; then
    echo "Cannot grab keyring source! Exiting."
    exit 1
fi

cp -rp ${GNUPG} ${TMPGNUPG}
chown -R root:root ${TMPGNUPG}
chmod 700 ${TMPGNUPG}
chmod 600 ${TMPGNUPG}/*

GNUPGHOME=${TMPGNUPG} gpg --import < \
    ${KEYRING}/${KEYRING_PACKAGE}/keyrings/ubuntu-archive-keyring.gpg

GNUPGHOME=${TMPGNUPG} gpg --yes --export \
    --output ${KEYRING}/${KEYRING_PACKAGE}/keyrings/ubuntu-archive-keyring.gpg \
    FBB75451 437D05B5 ${GPGKEYID}

(
    cd ${KEYRING}/${KEYRING_PACKAGE} && \
	dpkg-buildpackage -m"Mirantis Nailgun" -k"${GPGKEYID}" -uc -us
)

rm -f ${NEW}/pools/${RELEASE}/main/ubuntu-keyring*deb
cp ${KEYRING}/ubuntu-keyring*deb ${NEW}/pools/${RELEASE}/main || \
    { echo "Error occured while moving rebuilded ubuntu-keyring packages into pool"; exit 1; }


###########################
# UPDATING REPO
###########################

for s in ${SECTIONS}; do
    for a in ${ARCHITECTURES}; do
	for t in deb udeb; do
	    [ X${t} = Xudeb ] && di="/debian-installer" || di=""
	    mkdir -p ${NEW}/dists/${RELEASE}/${s}${di}/binary-${a}

	    if [ X${t} = Xdeb ]; then
		cat > ${NEW}/dists/${RELEASE}/${s}/binary-${a}/Release <<EOF
Archive: ${RELEASE}
Version: ${VERSION}
Component: ${s}
Origin: Mirantis
Label: Mirantis
Architecture: ${a}
EOF
	    fi
	done
    done
done

cat > ${BASEDIR}/extraoverride.pl <<EOF
#!/usr/bin/env perl
while (<>) {
  chomp; next if /^ /;
  if (/^\$/ && defined(\$task)) {
    print "\$package Task \$task\n";
    undef \$package;
    undef \$task;
  } 
  (\$key, \$value) = split /: /, \$_, 2;
  if (\$key eq 'Package') {
    \$package = \$value;
  } 
  if (\$key eq 'Task') {
    \$task = \$value;
  }
}
EOF
chmod +x ${BASEDIR}/extraoverride.pl

gunzip -c ${NEW}/dists/${RELEASE}/main/binary-amd64/Packages.gz | \
    ${BASEDIR}/extraoverride.pl >> \
    ${INDICES}/override.${RELEASE}.extra.main

for s in ${SECTIONS}; do
    for a in ${ARCHITECTURES}; do
	for t in deb udeb; do
	    echo "Scanning section=${s} arch=${a} type=${t} ..."

	    if [ X${t} = Xudeb ]; then
		di="/debian-installer"
		diover=".debian-installer"
	    else
		di=""
		diover=""
	    fi

	    [ -r ${INDICES}/override.${RELEASE}.${s}${diover} ] && \
		override=${INDICES}/override.${RELEASE}.${s}${diover} || \
		unset override
	    [ -r ${INDICES}/override.${RELEASE}.extra.${s} ] && \
		extraoverride="-e ${INDICES}/override.${RELEASE}.extra.${s}" || \
		unset extraoverride

	    mkdir -p ${NEW}/pools/${RELEASE}/${s}

	    (
		cd ${NEW} && dpkg-scanpackages -m -a${a} -t${t} ${extraoverride} \
		    pools/${RELEASE}/${s} \
		    ${override} > \
		    ${NEW}/dists/${RELEASE}/${s}${di}/binary-${a}/Packages
	    )

	    gzip -c ${NEW}/dists/${RELEASE}/${s}${di}/binary-${a}/Packages > \
		${NEW}/dists/${RELEASE}/${s}${di}/binary-${a}/Packages.gz
	done
    done
done

echo "Creating main Release file in cdrom repo"

cat > ${BASEDIR}/release.conf <<EOF
APT::FTPArchive::Release::Origin "Mirantis";
APT::FTPArchive::Release::Label "Mirantis";
APT::FTPArchive::Release::Suite "${RELEASE}";
APT::FTPArchive::Release::Version "${VERSION}";
APT::FTPArchive::Release::Codename "${RELEASE}";
APT::FTPArchive::Release::Architectures "${ARCHITECTURES}";
APT::FTPArchive::Release::Components "${SECTIONS}";
APT::FTPArchive::Release::Description "Mirantis Nailgun Repo";
EOF


apt-ftparchive -c ${BASEDIR}/release.conf release ${NEW}/dists/${RELEASE} > \
    ${NEW}/dists/${RELEASE}/Release


echo "Signing main Release file in cdrom repo ..."
GNUPGHOME=${TMPGNUPG} gpg --yes --no-tty --default-key ${GPGKEYID} \
    --passphrase-file ${GPGPASSWDFILE} --output ${NEW}/dists/${RELEASE}/Release.gpg \
    -ba ${NEW}/dists/${RELEASE}/Release


###########################
# CREATING INITRD
###########################

echo "Creating zero file ${INITRD_FS} 1024 * ${INITRD_SIZE} bytes size ..."
dd if=/dev/zero of=${INITRD_FS} bs=1024 count=${INITRD_SIZE}
echo "Creating ext2 file system in ${INITRD_FS} ..."
mkfs.ext2 -F -m0 ${INITRD_FS}
echo "Creating loop directory to mount initrd file system ..."
mkdir -p ${INITRD_LOOP}
echo "Mounting ${INITRD_FS} to ${INITRD_LOOP}"
mount -o loop -t ext2 ${INITRD_FS} ${INITRD_LOOP}

###########################
# DEBOOTSTRAPING 
###########################

echo "Debootstraping ..."

[ -n "${DEBOOTSTRAP_INCLUDE}" ] && DEBOOTSTRAP_INCLUDE_OPTION=--include=${DEBOOTSTRAP_INCLUDE}
[ -n "${DEBOOTSTRAP_EXCLUDE}" ] && DEBOOTSTRAP_EXCLUDE_OPTION=--exclude=${DEBOOTSTRAP_EXCLUDE}

debootstrap --variant=minbase --components=main,restricted,universe,multiverse \
${DEBOOTSTRAP_INCLUDE_OPTION} \
${DEBOOTSTRAP_EXCLUDE_OPTION} \
--no-check-gpg \
--arch=amd64 ${RELEASE} ${INITRD_LOOP} file:${NEW}


###########################
# MODULES AND FIRMWARE 
###########################

echo "Extracting modules and firmware from packages ..."
mkdir -p ${INITRD_MODULES}
find ${NEW}/pools/${RELEASE} \( -name "linux-image*.deb" -o -name "linux-firmware*.deb" \) -exec dpkg -x {} ${INITRD_MODULES} \;

echo "Copying modules and firmware ..."
cp -r ${INITRD_MODULES}/lib/modules/* ${INITRD_LOOP}/lib/modules
cp -r ${INITRD_MODULES}/lib/firmware/* ${INITRD_LOOP}/lib/firmware


echo  "Updating modules.dep in order to fix modprobe errors ..."
for version in `ls -1 ${INITRD_LOOP}/lib/modules`; do
    depmod -b ${INITRD_LOOP} $version
done

###########################
# CONFIGURING SYSTEM
###########################

echo "Setting default password for root into r00tme ..." 
sed -i -e '/^root/c\root:$6$oC7haQNQ$LtVf6AI.QKn9Jb89r83PtQN9fBqpHT9bAFLzy.YVxTLiFgsoqlPY3awKvbuSgtxYHx4RUcpUqMotp.WZ0Hwoj.:15441:0:99999:7:::' ${INITRD_LOOP}/etc/shadow

echo "Adding root autologin on tty1 ..."
sed -i -e '/exec/c\exec /sbin/getty -8 -l /usr/bin/autologin 38400 tty1' ${INITRD_LOOP}/etc/init/tty1.conf

###########################
# INJECTING EXTRA FILES
###########################
echo "Syncing system ..."
cp -r ${SYNC}/* ${INITRD_LOOP}

NAILGUN_DIR=${INITRD_LOOP}/opt/nailgun

#echo "Injecting cookbooks and configs for chef-solo ..."
#mkdir -p ${NAILGUN_DIR}/solo
#cp ${SOLO}/solo.json ${NAILGUN_DIR}/solo/solo.json
#cp ${SOLO}/solo.rb ${NAILGUN_DIR}/solo/solo.rb

#echo "Disabling chef-client ..."
#chroot ${INITRD_LOOP} /usr/sbin/update-rc.d chef-client disable

echo "Injecting agent ..."
mkdir -p ${NAILGUN_DIR}/bin
cp -r ${REPO}/bin/agent ${NAILGUN_DIR}/bin

echo "Injecting bootstrap file..."
echo "bootstrap" > ${NAILGUN_DIR}/system_type

echo "Injecting bootstrap ssh key ..."
mkdir -p ${INITRD_LOOP}/root/.ssh
cp ${SSH}/id_rsa.pub ${INITRD_LOOP}/root/.ssh/authorized_keys 

echo "Removing cached debs ..."
rm ${INITRD_LOOP}/var/cache/apt/archives/*.deb

echo "Removing sources.list ..."
rm ${INITRD_LOOP}/etc/apt/sources.list

###########################
# UMOUNTING 
###########################

echo "Trying to umount initrd loop ..."
if (mount | grep -q `readlink -f ${INITRD_LOOP}`); then
    echo "Umounting ${INITRD_LOOP} ..."
    umount ${INITRD_LOOP}
fi

###########################
# LINKING 
###########################
echo "Gzipping initrd ..."
# gzip -9 -c ${INITRD_FS} > ${BOOTSTRAPDIR}/${INITRDGZ}.${STAMP}
# chmod 644 ${BOOTSTRAPDIR}/${INITRDGZ}.${STAMP}
gzip -9 -c ${INITRD_FS} > ${BOOTSTRAPDIR}/${INITRDGZ}
chmod 644 ${BOOTSTRAPDIR}/${INITRDGZ}

echo "Coping linux ..."
linuxfile=`ls -1 ${INITRD_MODULES}/boot/vmlinuz*generic | head -1`
# cp ${linuxfile} ${BOOTSTRAPDIR}/${LINUX}.${STAMP}
# chmod 644 ${BOOTSTRAPDIR}/${LINUX}.${STAMP}
cp ${linuxfile} ${BOOTSTRAPDIR}/${LINUX}
chmod 644 ${BOOTSTRAPDIR}/${LINUX}

# rm -f ${BOOTSTRAPDIR}/${INITRDGZ}.last
# rm -f ${BOOTSTRAPDIR}/${LINUX}.last
# (
#     cd ${BOOTSTRAPDIR}
#     ln -s ${INITRDGZ}.${STAMP} ${INITRDGZ}.last
#     ln -s ${LINUX}.${STAMP} ${LINUX}.last
# )
