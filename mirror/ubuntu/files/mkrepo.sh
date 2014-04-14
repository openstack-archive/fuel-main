#!/bin/bash
apt-get update
for pkg in $(cat /requirements-deb.txt | grep -Ev "^#"); do
	apt-get -dy install $pkg || exit 1
done
# Make structure and mocks for multiarch
for dir in binary-i386 binary-amd64; do 
	mkdir -p /repo/dists/precise/main/$dir /repo/dists/precise/main/debian-installer/$dir
	touch /repo/dists/precise/main/$dir/Packages /repo/dists/precise/main/debian-installer/$dir/Packages
done
mkdir -p /repo/pool/debian-installer /repo/pool/main
cd /repo/pool/debian-installer
# Grab every udeb
for udeb in $(wget -qO - http://mirror.yandex.ru/ubuntu/dists/precise/main/debian-installer/binary-amd64/Packages.bz2 | bzip2 -cd | sed -ne 's/^Filename: //p'); do
        wget -N http://mirror.yandex.ru/ubuntu/$udeb
done
# Get rid of urlencoded names
for i in $(ls | grep %) ; do mv $i $(echo $i | echo -e $(sed 's/%/\\x/g')) ; done
rm -f debootstrap*
#
# Borrow right one...
wget http://download.mirantis.com/precise-grizzly-fuel-3.2/pool/main/d/debootstrap/debootstrap-udeb_1.0.39_all.udeb
# Move all stuff to the our package pool
mv /var/cache/apt/archives/*deb /repo/pool/main
cd /repo/pool/main
# urlencode again
for i in $(ls | grep %) ; do mv $i $(echo $i | echo -e $(sed 's/%/\\x/g')) ; done
mkdir -p /repo/indices
cd /repo/indices
for idx in override.precise.main override.precise.extra.main override.precise.main.debian-installer ; do
	wget -N http://mirror.yandex.ru/ubuntu/indices/$idx
done
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
