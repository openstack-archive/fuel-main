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

define SANDBOX_UBUNTU
mkdir -p $(SANDBOX_UBUNTU)
sudo debootstrap --no-check-gpg --arch=$(UBUNTU_ARCH) $(UBUNTU_RELEASE) $(SANDBOX_UBUNTU) file://$(LOCAL_MIRROR)/ubuntu
sudo cp /etc/resolv.conf $(SANDBOX_UBUNTU)/etc/resolv.conf
# generate utf8 locale
sudo chroot $(SANDBOX_UBUNTU) /bin/sh -c 'locale-gen en_US.UTF-8; dpkg-reconfigure locales'
# setup apt
test -e $(SANDBOX_UBUNTU)/tmp/apt && rm -rf $(SANDBOX_UBUNTU)/tmp/apt
mkdir -p $(SANDBOX_UBUNTU)/tmp/apt
sudo cp -al $(LOCAL_MIRROR)/ubuntu/dists $(LOCAL_MIRROR)/ubuntu/pool $(SANDBOX_UBUNTU)/tmp/apt
echo "deb file:///tmp/apt $(UBUNTU_RELEASE) main" | sudo tee $(SANDBOX_UBUNTU)/etc/apt/sources.list
echo "APT::Get::AllowUnauthenticated 1;" | sudo tee $(SANDBOX_UBUNTU)/etc/apt/apt.conf.d/02mirantis-unauthenticated
sudo chroot $(SANDBOX_UBUNTU) apt-get update
# install more packages
sudo chroot $(SANDBOX_UBUNTU) apt-get update
test -n "$(SANDBOX_DEB_PKGS)" && sudo chroot $(SANDBOX_UBUNTU) apt-get install --yes $(SANDBOX_DEB_PKGS)
endef

define SANDBOX_UBUNTU_DOWN
sync
sudo umount $(SANDBOX_UBUNTU)/proc
endef
