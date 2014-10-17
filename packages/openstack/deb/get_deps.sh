#!/bin/bash

# Get runtime dependencies for rebuilt OpenStack components
# (yumdownloader replacement for Ubuntu)
# Script is meant to be executed from within Ubuntu chroot
# Input: /$COMPONENT.pkg.list - with list of rebuilt packages
# Output: downloaded runtime dependencies in /repo/download

mkdir -p /repo/download/
cat /*.pkg.list > /pkglist.txt
has_apt_errors=''
rm -f /apt-errors.log
while read pkg; do
        downloads_list="/downloads_${pkg}.list"
        if ! apt-get --print-uris --yes -qq install $pkg >"${downloads_list}" 2>>"/apt-errors.log"; then
                echo "package $pkg can not be installed" >>/apt-errors.log
                # run apt-get once more to get a verbose error message
                apt-get --print-uris --yes install $pkg >>/apt-errors.log 2>&1 || true
                has_apt_errors='yes'
        fi
        sed -i "${downloads_list}" -n -e "s/^'\([^']\+\)['].*$/\1/p"
done < /pkglist.txt

if [ -n "$has_apt_errors" ]; then
        echo 'some packages are not installable' >&2
        cat < /apt-errors.log >&2
        exit 1
fi

cat /downloads_*.list | sort | uniq > /repo/download/download_urls.list
rm /downloads_*.list /apt-errors.log /pkglist.txt
(cat /repo/download/download_urls.list | xargs -n1 -P4 wget -nv -P /repo/download/) || exit 1
mv /var/cache/apt/archives/*deb /repo/download/

# Dowmloaded dependencies may contain the same pre-built packages from master repository,
# so let's remove them

for pkg in `cat *.pkg.list`; do EXPR=".*"$pkg"_[^-]+-[^-]+.*" ; find /repo/download -regex $EXPR -delete ; done
