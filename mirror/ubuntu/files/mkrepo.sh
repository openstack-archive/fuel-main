#!/bin/bash
apt-get update
# linux-image-3.2.0-23 used for installer
apt-get -dy install linux-image-3.2.0-23

for pkg in $(cat /requirements-deb.txt); do
	apt-get -dy install $pkg || exit 1
done
# Make structure and mocks for multiarch
for dir in binary-i386 binary-amd64; do 
	mkdir -p /repo/dists/precise/main/$dir /repo/dists/precise/main/debian-installer/$dir
	touch /repo/dists/precise/main/$dir/Packages /repo/dists/precise/main/debian-installer/$dir/Packages
done
mkdir -p /repo/pool/debian-installer /repo/pool/main
cd /repo/pool/debian-installer

###################
# Grab every udeb
###################

wrkdir=`dirname $(pwd)`/`basename $(pwd)`

rm -f ${wrkdir}/UPackages.tmp ${wrkdir}/override.precise.main ${wrkdir}/override.precise.extra.main
touch ${wrkdir}/UPackages.tmp ${wrkdir}/override.precise.main ${wrkdir}/override.precise.extra.main

# Prepare temp apt dirs
[ -d ${wrkdir}/apt.tmp ] && rm -rf ${wrkdir}/apt.tmp
mkdir -p ${wrkdir}/apt.tmp/lists
mkdir -p ${wrkdir}/apt.tmp/sources
mkdir -p ${wrkdir}/apt.tmp/cache

# Extract all specified repos (except backports repo)
for list in /etc/apt/sources.list /etc/apt/sources.list.d/*.list; do
  for repo in `cat $list| grep -v backports | sed 's| \+|\||g' | grep "^deb|"`; do
     repourl=`echo $repo | awk -F '|' '{print $2}'`
     repodist=`echo $repo | awk -F '|' '{print $3}'`
     repos=`echo $repo | awk -F '|' '{for(i=4; i<=NF; ++i) {print $i}}'`
     for repo in $repos; do
       bz=${repourl}/dists/${repodist}/${repo}/debian-installer/binary-amd64/Packages.bz2
       echo "deb ${repourl} ${repodist} ${repo}/debian-installer" >> ${wrkdir}/apt.tmp/sources/sources.list
       wget -qO - $bz | bzip2 -cdq | sed -ne 's/^Package: //p' >> ${wrkdir}/UPackages.tmp
       # Getting indices
       wget -O - ${repourl}/indices/override.${repodist}.${repo} >> ${wrkdir}/override.precise.main
       wget -O - ${repourl}/indices/override.${repodist}.extra.${repo} >> ${wrkdir}/override.precise.extra.main
     done
  done
done

# Collect all udebs except packages with suffux generic or virtual
packages=`cat ${wrkdir}/UPackages.tmp | sort -u | egrep -v "generic|virtual"`

# Find latest udebs with suffux generic or virtual
gvpackages=`cat ${wrkdir}/UPackages.tmp | egrep "generic|virtual" | sed 's|[0-9]\+|[0-9]+|g' | sort -u`
for package in $gvpackages; do
  packages="$packages `cat ${wrkdir}/UPackages.tmp | egrep "generic|virtual" | egrep $package | sort -rV | head -1`"
done

# Find modules for 3.2.0-23 kernel (installer runs with this version)
for package in `cat ${wrkdir}/UPackages.tmp | egrep "generic|virtual" | grep 3.2.0-23`; do
  packages="$packages $package"
done

# Update apt temp cache
apt-get -o Dir::Etc::SourceParts="${wrkdir}/apt.tmp/sources/parts" \
        -o Dir::Etc::SourceList="${wrkdir}/apt.tmp/sources/sources.list" \
        -o Dir::State::Lists="${wrkdir}/apt.tmp/lists" \
        -o Dir::Cache="${wrkdir}/apt.tmp/cache" \
        update

# Download udebs
apt-get -o Dir::Etc::SourceParts="${wrkdir}/apt.tmp/sources/parts" \
        -o Dir::Etc::SourceList="${wrkdir}/apt.tmp/sources/sources.list" \
        -o Dir::State::Lists="${wrkdir}/apt.tmp/lists" \
        -o Dir::Cache="${wrkdir}/apt.tmp/cache" \
        download $packages

rm -f ${wrkdir}/UPackages.tmp
rm -rf ${wrkdir}/apt.tmp

# Get rid of urlencoded names
for i in $(ls | grep %) ; do mv $i $(echo $i | echo -e $(sed 's/%/\\x/g')) ; done
#rm -f debootstrap*

#
# Borrow right one...
#wget http://download.mirantis.com/precise-grizzly-fuel-3.2/pool/main/d/debootstrap/debootstrap-udeb_1.0.39_all.udeb

##########################################
# Move all stuff to the our package pool
##########################################
mv /var/cache/apt/archives/*deb /repo/pool/main
cd /repo/pool/main
# urlencode again
for i in $(ls | grep %) ; do mv $i $(echo $i | echo -e $(sed 's/%/\\x/g')) ; done
mkdir -p /repo/indices
cd /repo/indices
for idx in override.precise.main override.precise.extra.main override.precise.main.debian-installer ; do
  cat ${wrkdir}/$idx | sort -u > /repo/indices/$idx
done
rm -f ${wrkdir}/override.precise.main ${wrkdir}/override.precise.extra.main ${wrkdir}/override.precise.main.debian-installer
cd /repo
# Just because apt scan will produce crap
cp -a Release-amd64 Release-i386
sed -i 's/amd64/i386/g' Release-i386
for amd64dir in $(find . -name binary-amd64) ; do
	cp -a Release-amd64 $amd64dir/Release
done
for i386dir in $(find . -name binary-i386) ; do
        cp -a Release-i386 $i386dir/Release
done
apt-ftparchive -c apt-ftparchive-release.conf generate apt-ftparchive-deb.conf
apt-ftparchive -c apt-ftparchive-release.conf generate apt-ftparchive-udeb.conf
apt-ftparchive -c apt-ftparchive-release.conf release dists/precise/ > dists/precise/Release
# some cleanup...
rm -rf apt-ftparchive*conf Release-amd64 Release-i386 mkrepo.sh preferences
