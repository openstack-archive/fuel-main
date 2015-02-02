#!/bin/bash

splitrepos="mos-plus mos-ubuntu"
[ ! -z "${EXTRA_DEB_REPOS}" ] && splitrepos=$splitrepos" extra-ubuntu" 

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

mkdir -p /repo/download/{mos-plus,mos-ubuntu}/{main,universe,multiverse}
[ ! -z "${EXTRA_DEB_REPOS}" ] && mkdir -p /repo/download/extra-ubuntu/{main,universe,multiverse}

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
	cat /tmp/essential.pkgs >> /requirements-deb.txt
}

# Note: apt-get install --print-uris package
# is not going to print anything if the package is already installed. Thus
# the base packages will be omitted if we use the main APT/dpkg settings.
# Pretend that no package has been installed by creating an alternative APT
# state and configuration directories.
# Previously we used to copy all debs from the APT cache which is unreliable:
# - a wrong version of the package might be included
# - multiple revisions of the same package might be included
apt_altstate="/apt-altstate"
rm -rf "$apt_altstate"
apt_lists_dir="$apt_altstate/var/lib/apt/lists"
apt_cache_dir="$apt_altstate/var/cache/apt"
null_dpkg_status="$apt_altstate/var/lib/dpkg/status"

mkdir -p "$apt_lists_dir"
mkdir -p "$apt_cache_dir"
mkdir -p "${null_dpkg_status%/*}"
touch "${null_dpkg_status}"

apt_altstate_opts="-o APT::Get::AllowUnauthenticated=1"
apt_altstate_opts="${apt_altstate_opts} -o Dir::State::Lists=${apt_lists_dir}"
apt_altstate_opts="${apt_altstate_opts} -o Dir::State::status=${null_dpkg_status}"
apt_altstate_opts="${apt_altstate_opts} -o Dir::Cache=${apt_cache_dir}"

if ! apt-get $apt_altstate_opts update; then
	echo "mkrepo.sh: failed to populate alt apt state"
	exit 1
fi

requirements_add_essential_pkgs
has_apt_errors=''
rm -f /apt-errors.log
while read pkg; do
	downloads_list="/downloads_${pkg}.list"
	if ! apt-get $apt_altstate_opts --print-uris --yes -qq install $pkg >"${downloads_list}" 2>>"/apt-errors.log"; then
		echo "package $pkg can not be installed" >>/apt-errors.log
		# run apt-get once more to get a verbose error message
		apt-get $apt_altstate_opts --print-uris --yes install $pkg >>/apt-errors.log 2>&1 || true
		has_apt_errors='yes'
	fi
	sed -i "${downloads_list}" -n -e "s/^'\([^']\+\)['].*$/\1/p"
done < /requirements-deb.txt

if [ -n "$has_apt_errors" ]; then
	echo 'some packages are not installable' >&2
	cat < /apt-errors.log >&2
	exit 1
fi

rm -rf "$apt_altstate"

# Prepare download lists for separated repositories
cat /downloads_*.list | sort -u > /repo/download/download_urls.list
egrep "${MIRROR_UBUNTU}|${MIRROR_UBUNTU_SECURITY}" < /repo/download/download_urls.list > /repo/download/mos-plus.list
grep ${MIRROR_FUEL_UBUNTU} < /repo/download/download_urls.list > /repo/download/mos-ubuntu.list

if [ ! -z "${EXTRA_DEB_REPOS}" ]; then
	EXTRA_DEB_REPOS_SORT=`echo "${EXTRA_DEB_REPOS}" | tr '|' '\n' | awk {'print $1'}`
	for extra_repo in ${EXTRA_DEB_REPOS_SORT}; do
	grep $extra_repo /repo/download/download_urls.list >> /repo/download/extra-ubuntu.list
	done
fi

rm /downloads_*.list /apt-errors.log

# Get the list of packages from upstream ISO
wget -nv -O /repo/download/iso.list http://releases.ubuntu.com/${UBUNTU_RELEASE_FULL}/ubuntu-${UBUNTU_RELEASE_FULL}-server-${UBUNTU_ARCH}.list || exit 1

# Filter out packages that exist on upstream ISO
cat /repo/download/iso.list | rev | cut -d"/" -f1 | rev | grep "\.deb$" > /repo/download/iso_filtered.list
grep -v -f /repo/download/iso_filtered.list /repo/download/mos-plus.list > /repo/download/mos-plus_filtered.list
grep "\/main\/" < /repo/download/mos-plus_filtered.list > /repo/download/mos-plus_filtered_main.list
grep "\/universe\/" < /repo/download/mos-plus_filtered.list > /repo/download/mos-plus_filtered_universe.list
grep "\/multiverse\/" < /repo/download/mos-plus_filtered.list > /repo/download/mos-plus_filtered_multiverse.list

for component in main universe multiverse; do
(cat /repo/download/mos-plus_filtered_$component.list | xargs -n1 -P4 wget -nv -P /repo/download/mos-plus/$component) || exit 1
done

# !!! only for prototype - to be replaced with wget/rsync/etc
(cat /repo/download/mos-ubuntu.list | xargs -n1 -P4 wget -nv -P /repo/download/mos-ubuntu/main) || exit 1
# !!! only for prototype - to be replaced with wget/rsync/etc

if [ ! -z "${EXTRA_DEB_REPOS}" ]; then
(cat /repo/download/extra-ubuntu.list | xargs -n1 -P4 wget -nv -P /repo/download/extra-ubuntu/main) || exit 1
fi

# cut out Fuel packages from mos-ubuntu
for fuelpkg in `cat /tmp/fuel.list`; do rm -f /repo/download/mos-ubuntu/main/$fuelpkg* ; done

# Make structure and mocks for multiarch
for repo in $splitrepos; do
for dir in binary-i386 binary-amd64; do
	mkdir -p /repo/$repo/dists/${UBUNTU_RELEASE}/{main,universe,multiverse}/$dir
	touch /repo/$repo/dists/${UBUNTU_RELEASE}/{main,universe,multiverse}/$dir/Packages
done
mkdir -p /repo/$repo/pool/{main,universe,multiverse}
done

###########################
# Get indices & other stuff
###########################

wrkdir=`dirname $(pwd)`/`basename $(pwd)`

rm -f ${wrkdir}/override.${UBUNTU_RELEASE}.main ${wrkdir}/override.${UBUNTU_RELEASE}.extra.main
touch ${wrkdir}/override.${UBUNTU_RELEASE}.main ${wrkdir}/override.${UBUNTU_RELEASE}.extra.main

# Prepare temp apt dirs
[ -d ${wrkdir}/apt.tmp ] && rm -rf ${wrkdir}/apt.tmp
mkdir -p ${wrkdir}/apt.tmp/lists
mkdir -p ${wrkdir}/apt.tmp/sources
mkdir -p ${wrkdir}/apt.tmp/cache

# Extract all specified repos (except backports repo)
for list in /etc/apt/sources.list; do
  for repo in `cat $list| grep -v backports | sed 's| \+|\||g' | grep "^deb|"`; do
     repourl=`echo $repo | awk -F '|' '{print $2}'`
     repodist=`echo $repo | awk -F '|' '{print $3}'`
     repos=`echo $repo | awk -F '|' '{for(i=4; i<=NF; ++i) {print $i}}'`
     for repo in $repos; do
       # Getting indices
       wget -nv -O - ${repourl}/indices/override.${repodist}.${repo} >> ${wrkdir}/override.${UBUNTU_RELEASE}.main
       wget -nv -O - ${repourl}/indices/override.${repodist}.extra.${repo} >> ${wrkdir}/override.${UBUNTU_RELEASE}.extra.main
     done
  done
done

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

####################################
# Move all stuff to our package pool
####################################
for repo in $splitrepos; do
    for component in main universe multiverse; do 
	mv /repo/download/$repo/$component/*deb /repo/$repo/pool/$component
	cd /repo/$repo/pool/$component
	# urlencode again
	for i in $(ls | grep %) ; do mv $i $(echo $i | echo -e $(sed 's/%/\\x/g')) ; done
    done
mkdir -p /repo/$repo/indices
cd /repo/$repo/indices
for idx in override.${UBUNTU_RELEASE}.main override.${UBUNTU_RELEASE}.extra.main; do
  cat ${wrkdir}/$idx | sort -u > /repo/$repo/indices/$idx
done
cd /repo/$repo
# Just because apt scan will produce crap
cp -a ../Release-amd64 ../apt-ftparchive*.conf .
sed -i "s/\/repo\//\/repo\/$repo\//g" apt-ftparchive*deb.conf
cp -a Release-amd64 Release-i386
sed -i 's/amd64/i386/g' Release-i386
for amd64dir in $(find . -name binary-amd64) ; do
	cp -a Release-amd64 $amd64dir/Release
done
for i386dir in $(find . -name binary-i386) ; do
        cp -a Release-i386 $i386dir/Release
done
apt-ftparchive -c apt-ftparchive-release.conf generate apt-ftparchive-deb.conf
# Work around the base system installation failure.
# XXX: someone should rewrite this script to use debmirror and reprepro
for pkg_file in `find dists -type f -name Packages`; do
	sort_packages_file $pkg_file
done
apt-ftparchive -c apt-ftparchive-release.conf release dists/${UBUNTU_RELEASE}/ > dists/${UBUNTU_RELEASE}/Release
rm -rf apt-ftparchive*conf Release-amd64 Release-i386
done

# some cleanup...
rm -f ${wrkdir}/override.${UBUNTU_RELEASE}.main ${wrkdir}/override.${UBUNTU_RELEASE}.extra.main
cd /repo ; rm -rf apt-ftparchive*conf Release-amd64 Release-i386 mkrepo.sh preferences
