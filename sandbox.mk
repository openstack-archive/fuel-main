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
mount | grep -q $(SANDBOX_UBUNTU)/proc || sudo mount -t proc none $(SANDBOX_UBUNTU)/proc
[ -f $(SANDBOX_UBUNTU)/etc/debian_version ]  || sudo multistrap -a amd64 -f $(SANDBOX_UBUNTU)/multistrap.conf -d $(SANDBOX_UBUNTU)/
sudo chroot $(SANDBOX_UBUNTU) /bin/bash -c "locale-gen en_US.UTF-8 ; dpkg-reconfigure locales"
sudo chroot $(SANDBOX_UBUNTU) /bin/bash -c "dpkg --configure -a || exit 0"
sudo chroot $(SANDBOX_UBUNTU) /bin/bash -c "rm -rf /var/run/*"
sudo chroot $(SANDBOX_UBUNTU) /bin/bash -c "dpkg --configure -a || exit 0"
echo 'APT::Get::AllowUnauthenticated 1;' | sudo tee $(SANDBOX_UBUNTU)/etc/apt/apt.conf.d/02mirantis-unauthenticated
[ -n "$(EXTRA_DEB_REPOS)" ] && echo "$(EXTRA_DEB_REPOS)" | tr '|' '\n' | while read repo; do echo deb $$repo; done  | sudo tee $(SANDBOX_UBUNTU)/etc/apt/sources.list.d/extra.list || exit 0
sudo cp /etc/resolv.conf $(SANDBOX_UBUNTU)/etc/resolv.conf
mount | grep -q $(SANDBOX_UBUNTU)/proc || sudo mount -t proc none $(SANDBOX_UBUNTU)/proc
endef

define SANDBOX_UBUNTU_DOWN
sync
sudo umount $(SANDBOX_UBUNTU)/proc
endef