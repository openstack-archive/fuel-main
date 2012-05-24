#!/bin/bash

set -x
set -e

[ X`whoami` = X'root' ] || { echo "You must be root."; exit 1; }

[ -z ${BUILDDIR} ] && BUILDDIR=/var/tmp/build_iso
echo "BUILDDIR=${BUILDDIR}"
[ -z ${REPODIR} ] && REPODIR=`dirname $0`/.. 
echo "REPODIR=${REPODIR}"

SCRIPTDIR=`dirname $0`

[ -z ${GNUPGHOME} ] && GNUPGHOME=${REPODIR}/gnupg

echo "Rebuilding ubuntu-keyring package in order to inject mirantis gpg key ..."
KEYRINGBUILDDIR=`mktemp -d`
mkdir -m 700 ${KEYRINGBUILDDIR}/gnupg
(cd ${KEYRINGBUILDDIR} && apt-get source ubuntu-keyring)
package=`find ${KEYRINGBUILDDIR} -type d -name "ubuntu-keyring*" | xargs basename`

cat ${REPODIR}/gnupg/pubring.gpg | \
    gpg --homedir ${KEYRINGBUILDDIR}/gnupg --import 2>/dev/null
cat ${KEYRINGBUILDDIR}/${package}/keyrings/ubuntu-archive-keyring.gpg | \
    gpg --homedir ${KEYRINGBUILDDIR}/gnupg --import 2>/dev/null
gpg --homedir ${KEYRINGBUILDDIR}/gnupg --export > \
    ${KEYRINGBUILDDIR}/${package}/keyrings/ubuntu-archive-keyring.gpg

(cd ${KEYRINGBUILDDIR}/${package} && dpkg-buildpackage || true )
mv ${KEYRINGBUILDDIR}/*.deb ${BUILDDIR}/pool/main/u/ubuntu-keyring
mv ${KEYRINGBUILDDIR}/*.udeb ${BUILDDIR}/pool/main/u/ubuntu-keyring
rm -r ${KEYRINGBUILDDIR}

# FIXME

echo "Downloading opscode packages ..."
MIRRORDOWNLOAD=http://mc0n1-srt.srt.mirantis.net/ubuntu/
TEMPDOWNLOAD=`mktemp --tmpdir=/var/tmp -d`
mkdir -p ${TEMPDOWNLOAD}/etc/preferences.d
mkdir -p ${TEMPDOWNLOAD}/etc/apt.conf.d
cat > ${TEMPDOWNLOAD}/etc/apt.conf <<EOF
APT
{
  Architecture "amd64";
  Default-Release "precise";
  Get::Download-Only "true";
  Get::AllowUnauthenticated "true";
};

Dir
{
  State "${TEMPDOWNLOAD}/state";
  State::status "status";
  
  Cache::archives "${TEMPDOWNLOAD}/archives";
  Cache "${TEMPDOWNLOAD}/cache";
  
  Etc "${TEMPDOWNLOAD}/etc";
};
EOF

cat > ${TEMPDOWNLOAD}/etc/sources.list <<EOF
deb ${MIRRORDOWNLOAD} precise main
EOF

mkdir -p ${TEMPDOWNLOAD}/state
touch ${TEMPDOWNLOAD}/state/status

mkdir -p ${TEMPDOWNLOAD}/archives
mkdir -p ${TEMPDOWNLOAD}/cache

apt-get -c=${TEMPDOWNLOAD}/etc/apt.conf update



echo "Updating repository ..."

DISTS=${BUILDDIR}/dists

rm -r ${DISTS}

mkdir -p ${DISTS}/precise/main/binary-amd64  
mkdir -p ${DISTS}/precise/main/binary-i386  
mkdir -p ${DISTS}/precise/main/debian-installer/binary-amd64  

(cd ${DISTS} && ln -s precise stable)
(cd ${DISTS} && ln -s precise unstable)

(cd ${BUILDDIR} && dpkg-scanpackages -m -a amd64 -tdeb pool | gzip -9c > dists/precise/main/binary-amd64/Packages.gz)
cat > ${DISTS}/precise/main/binary-amd64/Release <<EOF
Archive: precise
Version: 12.04
Component: main
Origin: Mirantis
Label: Mirantis Nailgun
Architecture: amd64
EOF

(cd ${BUILDDIR} && dpkg-scanpackages -m -a i386 -tdeb pool | gzip -9c > dists/precise/main/binary-i386/Packages.gz)
cat > ${DISTS}/precise/main/binary-amd64/Release <<EOF
Archive: precise
Version: 12.04
Component: main
Origin: Mirantis
Label: Mirantis Nailgun
Architecture: i386
EOF

(cd ${BUILDDIR} && dpkg-scanpackages -m -a amd64 -tudeb pool | gzip -9c > dists/precise/main/debian-installer/binary-amd64/Packages.gz)

TEMPCONF=`mktemp`

cat > ${TEMPCONF} <<EOF
APT::FTPArchive::Release::Origin "Mirantis";
APT::FTPArchive::Release::Label "Mirantis Nailgun";
APT::FTPArchive::Release::Codename "precise";
APT::FTPArchive::Release::Suite "precise";
APT::FTPArchive::Release::Version "12.04";
APT::FTPArchive::Release::Architectures "amd64 i386";
APT::FTPArchive::Release::Components "main";
APT::FTPArchive::Release::Description "Mirantis Nailgun Repo";
EOF

apt-ftparchive -c ${TEMPCONF} release ${DISTS}/precise > ${DISTS}/precise/Release

rm ${TEMPCONF}

echo "Signing Release ..."
GNUPGHOME=${GNUPGHOME} gpg --yes --output ${DISTS}/precise/Release.gpg -ba ${DISTS}/precise/Release

