define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=file://$(LOCAL_MIRROR_CENTOS_OS_BASEURL)
gpgcheck=0
enabled=1
endef

define sandbox_yum_conf
[main]
cachedir=$(SANDBOX)/cache
keepcache=0
debuglevel=6
logfile=$(SANDBOX)/yum.log
exclude=*.i686.rpm
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
pluginpath=$(SANDBOX)/etc/yum-plugins
pluginconfpath=$(SANDBOX)/etc/yum/pluginconf.d
reposdir=$(SANDBOX)/etc/yum.repos.d
endef

SANDBOX_PACKAGES:=bash

define SANDBOX_UP
echo "Starting SANDBOX up"
mkdir -p $(SANDBOX)/etc/yum.repos.d
cat > $(SANDBOX)/etc/yum.conf <<EOF
$(sandbox_yum_conf)
EOF
cp /etc/resolv.conf $(SANDBOX)/etc/resolv.conf
cat > $(SANDBOX)/etc/yum.repos.d/base.repo <<EOF
$(yum_local_repo)
EOF
rpm -i --root=$(SANDBOX) `find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name "centos-release*rpm" | head -1` || \
echo "centos-release already installed"
rm -f $(SANDBOX)/etc/yum.repos.d/Cent*
echo 'Rebuilding RPM DB'
rpm --root=$(SANDBOX) --rebuilddb
echo 'Installing packages for Sandbox'
yum -c $(SANDBOX)/etc/yum.conf --installroot=$(SANDBOX) -y --exclude=ruby-2.1.1 --nogpgcheck install $(SANDBOX_PACKAGES)
mount | grep -q $(SANDBOX)/proc || sudo mount --bind /proc $(SANDBOX)/proc
mount | grep -q $(SANDBOX)/dev || sudo mount --bind /dev $(SANDBOX)/dev
endef

define SANDBOX_DOWN
sync
umount $(SANDBOX)/proc
umount $(SANDBOX)/dev
endef

define SANDBOX_UBUNTU_UP
echo "SANDBOX_UBUNTU_UP: start"
mkdir -p $(SANDBOX_UBUNTU)
mkdir -p $(SANDBOX_UBUNTU)/usr/sbin
cat > $(SANDBOX_UBUNTU)/usr/sbin/policy-rc.d <<EOF
#!/bin/sh
# suppress services start in the staging chroots
exit 101
EOF
chmod 755 $(SANDBOX_UBUNTU)/usr/sbin/policy-rc.d
mkdir -p $(SANDBOX_UBUNTU)/etc/init.d
touch $(SANDBOX_UBUNTU)/etc/init.d/.legacy-bootordering
echo "Running debootstrap"
sudo debootstrap --no-check-gpg --arch=$(UBUNTU_ARCH) $(UBUNTU_RELEASE) $(SANDBOX_UBUNTU) file://$(LOCAL_MIRROR)/ubuntu
sudo cp /etc/resolv.conf $(SANDBOX_UBUNTU)/etc/resolv.conf
echo "Generating utf8 locale"
sudo chroot $(SANDBOX_UBUNTU) /bin/sh -c 'locale-gen en_US.UTF-8; dpkg-reconfigure locales'
echo "Preparing directory for chroot local mirror"
sudo mkdir -p $(SANDBOX_UBUNTU)/tmp/apt
echo "Bind mounting local Ubuntu mirror to $(SANDBOX_UBUNTU)/tmp/apt"
sudo mount -o bind $(LOCAL_MIRROR)/ubuntu $(SANDBOX_UBUNTU)/tmp/apt
sudo mount -o remount,ro,bind $(SANDBOX_UBUNTU)/tmp/apt
echo "Configuring apt sources.list: deb file:///tmp/apt $(UBUNTU_RELEASE) main"
echo "deb file:///tmp/apt $(UBUNTU_RELEASE) main" | sudo tee $(SANDBOX_UBUNTU)/etc/apt/sources.list
echo "Allowing using unsigned repos"
echo "APT::Get::AllowUnauthenticated 1;" | sudo tee $(SANDBOX_UBUNTU)/etc/apt/apt.conf.d/02mirantis-unauthenticated
echo "Updating apt package database"
sudo chroot $(SANDBOX_UBUNTU) apt-get update
echo "Installing additional packages: $(SANDBOX_DEB_PKGS)"
test -n "$(SANDBOX_DEB_PKGS)" && sudo chroot $(SANDBOX_UBUNTU) apt-get install --yes $(SANDBOX_DEB_PKGS)
echo "SANDBOX_UBUNTU_UP: done"
endef

define SANDBOX_UBUNTU_DOWN
if mountpoint -q $(SANDBOX_UBUNTU)/proc; then sudo umount $(SANDBOX_UBUNTU)/proc; fi
sudo umount $(SANDBOX_UBUNTU)/tmp/apt || true
endef
