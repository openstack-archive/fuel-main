#!/bin/bash

if [ -z "$UBUNTU_RELEASE" ]; then
	echo 'mkrepo.sh: UBUNTU_RELEASE is not defined'
	exit 1
fi

if [ -z "$UBUNTU_INSTALLER_KERNEL_VERSION" ]; then
	echo 'mkrepo.sh: UBUNTU_INSTALLER_KERNEL_VERSION is not defined'
	exit 1
fi

if [ -z "$UBUNTU_KERNEL_FLAVOR" ]; then
	echo 'mkrepo.sh UBUNTU_KERNEL_FLAVOR is not defined'
	exit 1
fi

mkdir -p /repo/download/

cat >> /requirements-deb.txt << EOF
linux-image-${UBUNTU_INSTALLER_KERNEL_VERSION}
linux-headers-${UBUNTU_INSTALLER_KERNEL_VERSION}
linux-image-generic-${UBUNTU_KERNEL_FLAVOR}
linux-headers-generic-${UBUNTU_KERNEL_FLAVOR}
EOF

requirements_add_essential_pkgs () {
	# All essential packages are already installed, so ask dpkg for a list
	dpkg-query -W -f='${Package} ${Essential}\n' > /tmp/essential.pkgs
	sed -i /tmp/essential.pkgs -n -e 's/\([^ ]\+\).*yes$/\1/p'
	cat /tmp/essential.pkgs /requirements-deb.txt | sort -u > /tmp/requirements-deb.txt
	mv /tmp/requirements-deb.txt /requirements-deb.txt
}

requirements_add_essential_pkgs
make -j4 -f /repo/mkrepo.mk deb_download || exit 1

# Make structure and mocks for multiarch
for dir in binary-i386 binary-amd64; do 
	mkdir -p /repo/dists/${UBUNTU_RELEASE}/main/$dir /repo/dists/${UBUNTU_RELEASE}/main/debian-installer/$dir
	touch /repo/dists/${UBUNTU_RELEASE}/main/$dir/Packages /repo/dists/${UBUNTU_RELEASE}/main/debian-installer/$dir/Packages
done
mkdir -p /repo/pool/debian-installer /repo/pool/main
cd /repo/pool/debian-installer

###################
# Grab every udeb
###################

apt_udeb_dir=/tmp/apt.udeb
rm -rf "${apt_udeb_dir}"
mkdir -p "${apt_udeb_dir}/lists"
mkdir -p "${apt_udeb_dir}/sources"
mkdir -p "${apt_udeb_dir}/cache"
touch ${apt_udeb_dir}/UPackages.tmp ${apt_udeb_dir}/override.${UBUNTU_RELEASE}.main ${apt_udeb_dir}/override.${UBUNTU_RELEASE}.extra.main


# Extract all specified repos (except backports repo)
for list in /etc/apt/sources.list; do
  for repo in `cat $list| grep -v backports | sed 's| \+|\||g' | grep "^deb|"`; do
     repourl=`echo $repo | awk -F '|' '{print $2}'`
     repodist=`echo $repo | awk -F '|' '{print $3}'`
     repos=`echo $repo | awk -F '|' '{for(i=4; i<=NF; ++i) {print $i}}'`
     for repo in $repos; do
       echo "deb ${repourl} ${repodist} ${repo}/debian-installer" >> "${apt_udeb_dir}/sources/sources.list"
       packagesfile=`wget -nv -qO - ${repourl}/dists/${repodist}/Release | \
                     egrep '[0-9a-f]{64}' | \
                     grep ${repo}/debian-installer/binary-amd64/Packages.bz2 | \
                     awk '{print $3}'`
       if [ -n "$packagesfile" ]; then
         bz=${repourl}/dists/${repodist}/$packagesfile
         wget -nv -qO - $bz | bzip2 -cdq | sed -ne 's/^Package: //p' >> ${apt_udeb_dir}/UPackages.tmp
       else
         bz=${repourl}/dists/${repodist}/${repo}/debian-installer/binary-amd64/Packages
         wget -nv -qO - $bz | sed -ne 's/^Package: //p' >> ${apt_udeb_dir}/UPackages.tmp
       fi
       # Getting indices
       wget -nv -O - ${repourl}/indices/override.${repodist}.${repo} >> ${apt_udeb_dir}/override.${UBUNTU_RELEASE}.main
       wget -nv -O - ${repourl}/indices/override.${repodist}.extra.${repo} >> ${apt_udeb_dir}/override.${UBUNTU_RELEASE}.extra.main
       wget -nv -O - ${repourl}/indices/override.${repodist}.${repo}.debian-installer >> ${apt_udeb_dir}/override.${UBUNTU_RELEASE}.main.debian-installer
     done
  done
done

# Collect all udebs except packages with suffux generic or virtual
packages=`sort -u < ${apt_udeb_dir}/UPackages.tmp | egrep -v "generic|virtual"`

# Find modules for ${UBUNTU_INSTALLER_KERNEL_VERSION} kernel (installer runs with this version)
for package in `cat ${apt_udeb_dir}/UPackages.tmp | egrep "generic|virtual" | grep ${UBUNTU_INSTALLER_KERNEL_VERSION}`; do
  packages="$packages $package"
done

apt_udeb_opts="-o Dir::Etc::SourceParts="${apt_udeb_dir}/sources/parts""
apt_udeb_opts="${apt_udeb_opts} -o Dir::Etc::SourceList="${apt_udeb_dir}/sources/sources.list""
apt_udeb_opts="${apt_udeb_opts} -o Dir::State::Lists="${apt_udeb_dir}/lists""
apt_udeb_opts="${apt_udeb_opts} -o Dir::Cache="${apt_udeb_dir}/cache""

# Update apt temp cache
apt-get ${apt_udeb_opts} update
# Download udebs
apt-get ${apt_udeb_opts} download $packages

# Get rid of urlencoded names
for i in $(ls | grep %) ; do mv $i $(echo $i | echo -e $(sed 's/%/\\x/g')) ; done

sort_packages_file () {
	local pkg_file="$1"
	local pkg_file_gz="${pkg_file}.gz"
	local pkg_file_bz2="${pkg_file}.bz2"
	apt-sortpkgs "$pkg_file" > "${pkg_file}.new" || exit 1
	if [ -e "$pkg_file_gz" ]; then
		gzip -c "${pkg_file}.new" > "$pkg_file_gz"
	fi
	if [ -e "$pkg_file_bz2" ]; then
		bzip2 -k "${pkg_file}.new" > "$pkg_file_bz2"
	fi
	mv "${pkg_file}.new" "${pkg_file}"
}

##########################################
# Move all stuff to the our package pool
##########################################
mv /repo/download/*deb /repo/pool/main
cd /repo/pool/main
# urlencode again
for i in $(ls | grep %) ; do mv $i $(echo $i | echo -e $(sed 's/%/\\x/g')) ; done
mkdir -p /repo/indices
cd /repo/indices
for idx in override.${UBUNTU_RELEASE}.main override.${UBUNTU_RELEASE}.extra.main override.${UBUNTU_RELEASE}.main.debian-installer; do
  cat ${apt_udeb_dir}/$idx | sort -u > /repo/indices/$idx
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
# Work around the base system installation failure.
# XXX: someone should rewrite this script to use debmirror and reprepro
for pkg_file in `find dists -type f -name Packages`; do
	sort_packages_file $pkg_file
done
apt-ftparchive -c apt-ftparchive-release.conf release dists/${UBUNTU_RELEASE}/ > dists/${UBUNTU_RELEASE}/Release
