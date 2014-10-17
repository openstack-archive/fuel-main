#!/bin/bash

apt-get update
mkdir -p /repo/download/
cat /pkg.list | while read pkg; do apt-get --print-uris --yes install $pkg | grep ^\' | cut -d\' -f2 >/downloads_$pkg.list; done
cat /downloads_*.list | sort | uniq > /repo/download/download_urls.list
(cat /repo/download/download_urls.list | xargs -n1 -P4 wget -nv -P /repo/download/) || exit 1
# remove duplicate packages from downloaded deps
for i in `cat /pkg.list`; do rm -f /repo/download/*$i*; done
rm /downloads_*.list /pkg.list
mv /var/cache/apt/archives/*deb /repo/download/
