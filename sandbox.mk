.PHONY: show-centos-sandbox-repos

define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=file://$(LOCAL_MIRROR_REDOS_OS_BASEURL)
gpgcheck=0
enabled=1
priority=10
endef
define yum_upstream_repo
[upstream]
name=Upstream mirror
baseurl=$(SANDBOX_MIRROR_REDOS_UPSTREAM)/os/$(REDOS_ARCH)/
gpgcheck=0
priority=1
[upstream-updates]
name=Upstream mirror
baseurl=$(SANDBOX_MIRROR_REDOS_UPSTREAM)/updates/$(REDOS_ARCH)/
gpgcheck=0
priority=1
endef
define yum_epel_repo
[epel]
name=epel mirror
baseurl=$(SANDBOX_MIRROR_EPEL)/$(REDOS_MAJOR)/$(REDOS_ARCH)/
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
sudo rpm -i --root=$(SANDBOX) `find $(LOCAL_MIRROR_REDOS_OS_BASEURL) -name "redos-release*rpm" | head -1` || \
echo "centos-release already installed"
sudo rm -f $(SANDBOX)/etc/yum.repos.d/RedOS*
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

#Extra repositories
$(if $(EXTRA_DEB_REPOS),$(subst |,$(newline)deb ,deb $(EXTRA_DEB_REPOS)))
endef

show-redos-sandbox-repos: export sandbox_yum_conf_content:=$(sandbox_yum_conf)
show-redos-sandbox-repos: export yum_upstream_repo_content:=$(yum_upstream_repo)
show-redos-sandbox-repos: export yum_epel_repo_content:=$(yum_epel_repo)
show-redos-sandbox-repos: export yum_local_repo_content:=$(yum_local_repo)
show-redos-sandbox-repos:
	/bin/echo -e "$${sandbox_yum_conf_content}\n"
	/bin/echo -e "$${yum_upstream_repo_content}\n"
	/bin/echo -e "$${yum_epel_repo_content}\n"
	/bin/echo -e "$${yum_local_repo_content}\n"
