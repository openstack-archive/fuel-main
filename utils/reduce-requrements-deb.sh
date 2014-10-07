#!/bin/sh
set -e
myname="reduce-requirements-deb"
initial_pkgs="$@"

if [ -z "$initial_pkgs" ]; then
	echo "$myname: no initial packages specified"
	exit 0
fi

cd "$(dirname $0)/.."

cfg_UBUNTU_RELEASE=`sed -n -e '/^UBUNTU_RELEASE/ { s/^UBUNTU_RELEASE:=//p }' config.mk`
cfg_MIRROR_UBUNTU=`sed -n -e '/^MIRROR_UBUNTU.[=]http/ { s/^MIRROR_UBUNTU.[=]//p }' config.mk`
PRODUCT_VERSION=`sed -n -e '/^PRODUCT_VERSION/ { s/^PRODUCT_VERSION:=//p }' config.mk`
MIRROR_FUEL_UBUNTU="http://osci-obs.vm.mirantis.net:82/ubuntu-fuel-${PRODUCT_VERSION}-stable/reprepro"

if [ -z "$MIRROR_UBUNTU" ]; then
	MIRROR_UBUNTU="$cfg_MIRROR_UBUNTU"
fi
if [ -z "$UBUNTU_RELEASE" ]; then
	UBUNTU_RELEASE="$cfg_UBUNTU_RELEASE"
fi

rm -rf germinate seeds </dev/null >/dev/null
mkdir germinate seeds 

touch seeds/blacklist
touch seeds/supported
cat > seeds/STRUCTURE << EOF
required:
supported:
EOF

for pkg in $initial_pkgs; do
	echo " * $pkg"
done > seeds/required

old_pwd="`pwd`"
cd germinate

germinate -v \
	-m "$MIRROR_UBUNTU" \
	-m "$MIRROR_FUEL_UBUNTU" \
	-d $UBUNTU_RELEASE \
	-a amd64 \
	-c main,universe,multiverse \
	-s seeds \
	-S "file://${old_pwd}"

cd ..

sed -n -e '/^--------/,/^---------/ { s/^\([a-z][^ \t]\+\).*$/\1/p }' germinate/required.depends > packages-expanded.tmp
sort < packages-expanded.tmp > packages-expanded.txt
sort < requirements-deb.txt > requirements-deb-sorted.txt
comm -23 requirements-deb-sorted.txt packages-expanded.txt > requirements-deb-reduced.txt

