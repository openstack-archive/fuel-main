define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=$(SANDBOX_MIRROR_TO_USE)
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
# download centos-release
yumdownloader --resolve --archlist=$(CENTOS_ARCH) \
-c $(SANDBOX)/etc/yum.conf \
--destdir=$(BUILD_DIR)/packages/rpm/ centos-release
sudo rpm -i --root=$(SANDBOX) `find $(BUILD_DIR)/packages/rpm/ -maxdepth 1 -name "centos-release*rpm" | head -1` || \
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
