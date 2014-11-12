#!/bin/sh

# SANDBOX_UBUNTU: create chroot here
# SANDBOX_DEB_PKGS: packages to install into the chroot
# UBUNTU_RELEASE: Ubuntu release codename ('precise', 'trusty', etc)
# LOCAL_MIRROR: path to the locally created APT repo
set -e

local_apt_repo="/tmp/apt"

install_more_packages () {
	sudo chroot ${SANDBOX_UBUNTU} apt-get update
	sudo chroot ${SANDBOX_UBUNTU} apt-get install --yes $@
}

hardlink_local_apt_repo () {
	# XXX: consider read-only bind mounts instead
	local new_apt_repo="$SANDBOX_UBUNTU/$local_apt_repo"
	rm -rf $new_apt_repo >/dev/null 2>&1 || true 
	mkdir -p $new_apt_repo
	sudo cp -al $LOCAL_MIRROR/ubuntu/dists $LOCAL_MIRROR/ubuntu/pool $new_apt_repo
}

apt_setup () {
	hardlink_local_apt_repo
	sudo /bin/sh -c "cat > $SANDBOX_UBUNTU/etc/apt/sources.list" <<-EOF
	deb file://${local_apt_repo} ${UBUNTU_RELEASE} main
	EOF
	sudo /bin/sh -c "cat > ${SANDBOX_UBUNTU}/etc/apt/apt.conf.d/02mirantis-unauthenticated" <<-EOF
	APT::Get::AllowUnauthenticated 1;
	EOF
	sudo chroot $SANDBOX_UBUNTU apt-get update
}

generate_utf8_locale () {
	sudo chroot $SANDBOX_UBUNTU /bin/sh -c \
		'locale-gen en_US.UTF-8; dpkg-reconfigure locales'
}

maybe_mount_chroot_proc () {
	if ! mountpoint -q ${SANDBOX_UBUNTU}/proc; then
		sudo mount -t proc sandbox_ubuntu_proc ${SANDBOX_UBUNTU}/proc
	fi
}

create_basic_chroot () {
	sudo debootstrap \
		--no-check-gpg \
		--arch=$UBUNTU_ARCH \
		$UBUNTU_RELEASE $SANDBOX_UBUNTU file://${LOCAL_MIRROR}/ubuntu
	sudo cp /etc/resolv.conf ${SANDBOX_UBUNTU}/etc/resolv.conf
	generate_utf8_locale
	apt_setup
	install_more_packages $SANDBOX_DEB_PKGS
}

if [ ! -f ${SANDBOX_UBUNTU}/etc/debian_version ]; then
	create_basic_chroot
fi
maybe_mount_chroot_proc

