.PHONY: show-ubuntu-sandbox-repos show-centos-sandbox-repos

define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=file://$(LOCAL_MIRROR_CENTOS_OS_BASEURL)
gpgcheck=0
enabled=1
priority=10
endef
define yum_upstream_repo
[upstream]
name=Upstream mirror
baseurl=$(SANDBOX_MIRROR_CENTOS_UPSTREAM)/os/$(CENTOS_ARCH)/
gpgcheck=0
priority=1
[upstream-updates]
name=Upstream mirror
baseurl=$(SANDBOX_MIRROR_CENTOS_UPSTREAM)/updates/$(CENTOS_ARCH)/
gpgcheck=0
priority=1
endef
define yum_epel_repo
[epel]
name=epel mirror
baseurl=$(SANDBOX_MIRROR_EPEL)/$(CENTOS_MAJOR)/$(CENTOS_ARCH)/
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
cp /etc/hosts $(SANDBOX)/etc/hosts
cat > $(SANDBOX)/etc/yum.repos.d/base.repo <<EOF
$(yum_upstream_repo)
$(yum_epel_repo)
$(yum_local_repo)
EOF
mkdir -p $(SANDBOX)/etc/yum/pluginconf.d/
mkdir -p $(SANDBOX)/etc/yum-plugins/
cp $(SOURCE_DIR)/mirror/centos/yum-priorities-plugin.py $(SANDBOX)/etc/yum-plugins/priorities.py
cat > $(SANDBOX)/etc/yum/pluginconf.d/priorities.conf << EOF
[main]
enabled=1
check_obsoletes=1
full_match=1
EOF
sudo rpm -i --root=$(SANDBOX) `find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name "centos-release*rpm" | head -1` || \
echo "centos-release already installed"
sudo rm -f $(SANDBOX)/etc/yum.repos.d/Cent*
echo 'Rebuilding RPM DB'
sudo rpm --root=$(SANDBOX) --rebuilddb
echo 'Installing packages for Sandbox'
sudo /bin/sh -c 'export TMPDIR=$(SANDBOX)/tmp/yum TMP=$(SANDBOX)/tmp/yum; echo $(SANDBOX_PACKAGES) | xargs -n1 yum -c $(SANDBOX)/etc/yum.conf --installroot=$(SANDBOX) -y --nogpgcheck install'
mount | grep -q $(SANDBOX)/proc || sudo mount --bind /proc $(SANDBOX)/proc
mount | grep -q $(SANDBOX)/dev || sudo mount --bind /dev $(SANDBOX)/dev
endef

define SANDBOX_DOWN
sudo umount $(SANDBOX)/proc || true
sudo umount $(SANDBOX)/dev || true
endef

define apt_sources_list
#Upstream Ubuntu mirrors
deb $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_ROOT) $(MIRROR_UBUNTU_SUITE) $(MIRROR_UBUNTU_SECTION)
deb $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_ROOT) $(MIRROR_UBUNTU_SUITE)-updates $(MIRROR_UBUNTU_SECTION)
deb $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_ROOT) $(MIRROR_UBUNTU_SUITE)-security $(MIRROR_UBUNTU_SECTION)
# MOS repos
deb $(MIRROR_MOS_UBUNTU_METHOD)://$(MIRROR_MOS_UBUNTU)$(MIRROR_MOS_UBUNTU_ROOT) $(MIRROR_MOS_SANDBOX_UBUNTU_SUITE) $(MIRROR_MOS_UBUNTU_SECTION)
deb $(MIRROR_MOS_UBUNTU_METHOD)://$(MIRROR_MOS_UBUNTU)$(MIRROR_MOS_UBUNTU_ROOT) $(MIRROR_MOS_SANDBOX_UBUNTU_SUITE)-security $(MIRROR_MOS_UBUNTU_SECTION)
deb $(MIRROR_MOS_UBUNTU_METHOD)://$(MIRROR_MOS_UBUNTU)$(MIRROR_MOS_UBUNTU_ROOT) $(MIRROR_MOS_SANDBOX_UBUNTU_SUITE)-proposed $(MIRROR_MOS_UBUNTU_SECTION)
deb $(MIRROR_MOS_UBUNTU_METHOD)://$(MIRROR_MOS_UBUNTU)$(MIRROR_MOS_UBUNTU_ROOT) $(MIRROR_MOS_SANDBOX_UBUNTU_SUITE)-updates $(MIRROR_MOS_UBUNTU_SECTION)
deb $(MIRROR_MOS_UBUNTU_METHOD)://$(MIRROR_MOS_UBUNTU)$(MIRROR_MOS_UBUNTU_ROOT) $(MIRROR_MOS_SANDBOX_UBUNTU_SUITE)-holdback $(MIRROR_MOS_UBUNTU_SECTION)

#Extra repositories
$(if $(EXTRA_DEB_REPOS),$(subst |,$(newline)deb ,deb $(EXTRA_DEB_REPOS)))
endef

define apt_preferences
# Apt repo @ obs-1 has Codename=trusty (which is OK)
# However the one @ mirror.fuel-infra has Codename=mos6.1
Package: *
Pin: release o=Mirantis, n=$(MIRROR_UBUNTU_SUITE)
Pin-Priority: 1101

Package: *
Pin: release o=Mirantis, n=$(PRODUCT_NAME)$(PRODUCT_VERSION)
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
set -e
echo "SANDBOX_UBUNTU_UP: start"
mkdir -p $(SANDBOX_UBUNTU)
mkdir -p $(SANDBOX_UBUNTU)/usr/sbin
cat > $(BUILD_DIR)/policy-rc.d << EOF
#!/bin/sh
# suppress services start in the staging chroots
exit 101
EOF
chmod 755 $(BUILD_DIR)/policy-rc.d
mkdir -p $(SANDBOX_UBUNTU)/etc/init.d
touch $(SANDBOX_UBUNTU)/etc/init.d/.legacy-bootordering
mkdir -p $(SANDBOX_UBUNTU)/usr/sbin
cp -a $(BUILD_DIR)/policy-rc.d $(SANDBOX_UBUNTU)/usr/sbin
echo "Running debootstrap"
sudo debootstrap --no-check-gpg --include=ca-certificates --arch=$(UBUNTU_ARCH) $(MIRROR_UBUNTU_SUITE) $(SANDBOX_UBUNTU) $(MIRROR_UBUNTU_METHOD)://$(MIRROR_UBUNTU)$(MIRROR_UBUNTU_ROOT)
if [ -e $(SANDBOX_UBUNTU)/etc/resolv.conf ]; then sudo cp -a $(SANDBOX_UBUNTU)/etc/resolv.conf $(SANDBOX_UBUNTU)/etc/resolv.conf.orig; fi
sudo cp /etc/resolv.conf $(SANDBOX_UBUNTU)/etc/resolv.conf
if [ -e $(SANDBOX_UBUNTU)/etc/hosts ]; then sudo cp -a $(SANDBOX_UBUNTU)/etc/hosts $(SANDBOX_UBUNTU)/etc/hosts.orig; fi
sudo cp /etc/hosts $(SANDBOX_UBUNTU)/etc/hosts
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
sudo cp $(BUILD_DIR)/policy-rc.d $(SANDBOX_UBUNTU)/usr/sbin
echo "Allowing using unsigned repos"
echo "APT::Get::AllowUnauthenticated 1;" | sudo tee $(SANDBOX_UBUNTU)/etc/apt/apt.conf.d/02mirantis-unauthenticated
if [ "$(SANDBOX_COPY_CERTS)" = "1" ] ; then
echo "Copying local certificates and CA to chroot"
sudo bash -c "mkdir -p $(SANDBOX_UBUNTU)/usr/share/ca-certificates/ ; rsync -arzL /etc/ssl/certs/ $(SANDBOX_UBUNTU)/usr/share/ca-certificates/local/"
echo "Acquire::https {  Verify-Peer \"true\";  Verify-Host \"true\"; }; " | sudo tee -a $(SANDBOX_UBUNTU)/etc/apt/apt.conf.d/05-local-ssl-certs
sudo chroot $(SANDBOX_UBUNTU) sh -xc "(cd  /usr/share/ca-certificates; find local -type f) >> /etc/ca-certificates.conf"
sudo chroot $(SANDBOX_UBUNTU) update-ca-certificates
fi
echo "Updating apt package database"
sudo chroot $(SANDBOX_UBUNTU) bash -c "(mkdir -p '$${TEMP}'; mkdir -p /tmp/user/0)"
sudo chroot $(SANDBOX_UBUNTU) apt-get update
if ! mountpoint -q $(SANDBOX_UBUNTU)/proc; then sudo mount -t proc sandboxproc $(SANDBOX_UBUNTU)/proc; fi
echo "Installing additional packages: $(SANDBOX_DEB_PKGS)"
sudo chroot $(SANDBOX_UBUNTU) apt-get dist-upgrade --yes
test -n "$(SANDBOX_DEB_PKGS)" && sudo chroot $(SANDBOX_UBUNTU) env LC_ALL=C DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true apt-get install --yes $(SANDBOX_DEB_PKGS)
echo "SANDBOX_UBUNTU_UP: done"
endef

define SANDBOX_UBUNTU_DOWN
	if mountpoint -q $(SANDBOX_UBUNTU)/proc; then sudo umount $(SANDBOX_UBUNTU)/proc; fi
	sudo umount $(SANDBOX_UBUNTU)/tmp/apt || true
endef

show-ubuntu-sandbox-repos: export apt_source_content:=$(apt_sources_list)
show-ubuntu-sandbox-repos: export apt_pinning_content:=$(apt_preferences)
show-ubuntu-sandbox-repos:
	/bin/echo -e "$${apt_source_content}"
	/bin/echo -e "$${apt_pinning_content}"

show-centos-sandbox-repos: export sandbox_yum_conf_content:=$(sandbox_yum_conf)
show-centos-sandbox-repos: export yum_upstream_repo_content:=$(yum_upstream_repo)
show-centos-sandbox-repos: export yum_epel_repo_content:=$(yum_epel_repo)
show-centos-sandbox-repos: export yum_local_repo_content:=$(yum_local_repo)
show-centos-sandbox-repos:
	/bin/echo -e "$${sandbox_yum_conf_content}\n"
	/bin/echo -e "$${yum_upstream_repo_content}\n"
	/bin/echo -e "$${yum_epel_repo_content}\n"
	/bin/echo -e "$${yum_local_repo_content}\n"
