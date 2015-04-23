define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=file://$(LOCAL_MIRROR_CENTOS_OS_BASEURL)
gpgcheck=0
enabled=1
priority=1
endef
define yum_upstream_repo
[upstream]
name=Upstream mirror
baseurl=$(SANDBOX_MIRROR_CENTOS_UPSTREAM_OS_BASEURL)
gpgcheck=0
priority=2
[upstream-updates]
name=Upstream mirror
baseurl=$(SANDBOX_MIRROR_CENTOS_UPDATES_OS_BASEURL)
gpgcheck=0
priority=2
endef
define yum_epel_repo
[epel]
name=epel mirror
baseurl=$(SANDBOX_MIRROR_EPEL_OS_BASEURL)
gpgcheck=0
priority=3
endef
define sandbox_yum_conf
[main]
cachedir=$(SANDBOX)/cache
keepcache=0
debuglevel=2
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

SANDBOX_PACKAGES:=bash yum

define SANDBOX_UP
echo "Starting SANDBOX up"
mkdir -p $(SANDBOX)/etc/yum.repos.d
cat > $(SANDBOX)/etc/yum.conf <<EOF
$(sandbox_yum_conf)
EOF
cp /etc/resolv.conf $(SANDBOX)/etc/resolv.conf
cat > $(SANDBOX)/etc/yum.repos.d/base.repo <<EOF
$(yum_upstream_repo)
$(yum_epel_repo)
$(yum_local_repo)
EOF
sudo rpm -i --root=$(SANDBOX) `find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name "centos-release*rpm" | head -1` || \
echo "centos-release already installed"
sudo rm -f $(SANDBOX)/etc/yum.repos.d/Cent*
echo 'Rebuilding RPM DB'
sudo rpm --root=$(SANDBOX) --rebuilddb
echo 'Installing packages for Sandbox'
sudo /bin/sh -c 'export TMPDIR=$(SANDBOX)/tmp/yum TMP=$(SANDBOX)/tmp/yum; yum -c $(SANDBOX)/etc/yum.conf --installroot=$(SANDBOX) -y --nogpgcheck install $(SANDBOX_PACKAGES)'
mount | grep -q $(SANDBOX)/proc || sudo mount --bind /proc $(SANDBOX)/proc
mount | grep -q $(SANDBOX)/dev || sudo mount --bind /dev $(SANDBOX)/dev
endef

define SANDBOX_DOWN
sudo umount $(SANDBOX)/proc || true
sudo umount $(SANDBOX)/dev || true
endef


define apt_sources_list
#Upstream Ubuntu mirrors
deb $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_SUFFIX) $(UBUNTU_RELEASE) main universe multiverse restricted
deb $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_SUFFIX) $(UBUNTU_RELEASE)-updates main universe multiverse restricted
deb $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_SUFFIX) $(UBUNTU_RELEASE)-security main universe multiverse restricted
#MOS mirrors
deb $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_ROOT) $(PRODUCT_NAME)$(PRODUCT_VERSION) main restricted
deb $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_ROOT) $(PRODUCT_NAME)$(PRODUCT_VERSION)-security main restricted
deb $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_ROOT) $(PRODUCT_NAME)$(PRODUCT_VERSION)-proposed main restricted
deb $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_ROOT) $(PRODUCT_NAME)$(PRODUCT_VERSION)-updates main restricted
deb $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_ROOT) $(PRODUCT_NAME)$(PRODUCT_VERSION)-holdback main restricted
#Extra repositories
$(if $(EXTRA_DEB_REPOS),$(subst |,$(newline)deb ,deb $(EXTRA_DEB_REPOS)))
endef

define apt_preferences
Package: *
Pin: origin download.mirantis.com
Pin-Priority: 1001

Package: *
Pin: release o=Mirantis, n=$(UBUNTU_RELEASE)
Pin-Priority: 1101

# to install packages from unmerged fuel-infra requests
Package: *
Pin: release l=$(UBUNTU_RELEASE)-fuel-$(PRODUCT_VERSION)-stable*
Pin-Priority: 1101

Package: *
Pin: release o=Open Build Service $(UBUNTU_RELEASE)-fuel-$(PRODUCT_VERSION)-stable*
Pin-Priority: 1101
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
sudo debootstrap --no-check-gpg --arch=$(UBUNTU_ARCH) $(UBUNTU_RELEASE) $(SANDBOX_UBUNTU) http://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_SUFFIX)
sudo cp /etc/resolv.conf $(SANDBOX_UBUNTU)/etc/resolv.conf
echo "Generating utf8 locale"
sudo chroot $(SANDBOX_UBUNTU) /bin/sh -c 'locale-gen en_US.UTF-8; dpkg-reconfigure locales'
echo "Preparing directory for chroot local mirror"
sudo mkdir -p $(SANDBOX_UBUNTU)/etc/apt/preferences.d/
echo "Generating pinning file for Ubuntu SandBox"
cat > $(BUILD_DIR)/mirror/ubuntu/preferences << EOF
$(apt_preferences)
EOF
sudo cp $(BUILD_DIR)/mirror/ubuntu/preferences $(SANDBOX_UBUNTU)/etc/apt/preferences.d/
echo "Configuring apt sources.list"
cat > $(BUILD_DIR)/mirror/ubuntu/sources.list << EOF
$(apt_sources_list)
EOF
sudo cp $(BUILD_DIR)/mirror/ubuntu/sources.list $(SANDBOX_UBUNTU)/etc/apt/
echo "Allowing using unsigned repos"
echo "APT::Get::AllowUnauthenticated 1;" | sudo tee $(SANDBOX_UBUNTU)/etc/apt/apt.conf.d/02mirantis-unauthenticated
echo "Updating apt package database"
sudo chroot $(SANDBOX_UBUNTU) bash -c "(mkdir -p '$${TEMP}'; mkdir -p /tmp/user/0)"
sudo chroot $(SANDBOX_UBUNTU) apt-get update
echo "Installing additional packages: $(SANDBOX_DEB_PKGS)"
sudo chroot $(SANDBOX_UBUNTU) apt-get dist-upgrade --yes
test -n "$(SANDBOX_DEB_PKGS)" && sudo chroot $(SANDBOX_UBUNTU) apt-get install --yes $(SANDBOX_DEB_PKGS)
echo "SANDBOX_UBUNTU_UP: done"
endef

define SANDBOX_UBUNTU_DOWN
	if mountpoint -q $(SANDBOX_UBUNTU)/proc; then sudo umount $(SANDBOX_UBUNTU)/proc; fi
	sudo umount $(SANDBOX_UBUNTU)/tmp/apt || true
endef

