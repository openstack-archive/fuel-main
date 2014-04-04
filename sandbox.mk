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

SANDBOX_PACKAGES:=\
	byacc \
	flex \
	gcc \
	glibc-devel \
	glibc-headers \
	kernel-lt-headers \
	make \
	openssl-devel \
	postgresql-devel \
	python-devel.x86_64 \
	python-pip \
	rpm-build \
	ruby \
	ruby-devel \
	rubygem-rake \
	rubygems \
	tar \
	which \
	zlib-devel


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
yum -c $(SANDBOX)/etc/yum.conf --installroot=$(SANDBOX) -y --exclude=ruby-2.1.1-1.1.x86_64 --nogpgcheck install $(SANDBOX_PACKAGES)
mount | grep -q $(SANDBOX)/proc || sudo mount --bind /proc $(SANDBOX)/proc
mount | grep -q $(SANDBOX)/dev || sudo mount --bind /dev $(SANDBOX)/dev
endef

define SANDBOX_DOWN
sync
umount $(SANDBOX)/proc
umount $(SANDBOX)/dev
endef
