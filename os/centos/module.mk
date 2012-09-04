/:=$(BUILD_DIR)/packages/centos/

$/%: /:=$/

REPOMIRROR:=$(MIRROR_URL)/centos
CENTOSMIRROR:=http://mirror.yandex.ru/centos
EPELMIRROR:=http://mirror.yandex.ru/epel
RPMFORGEMIRROR:=http://apt.sw.be/redhat

CENTOSMIN_PACKAGES:=$(shell grep "<packagereq type='mandatory'>" os/centos/comps.xml | sed -e "s/^\s*<packagereq type='mandatory'>\(.*\)<\/packagereq>\s*$$/\\1/")
CENTOSEXTRA_PACKAGES:=$(shell grep -v ^\\s*\# requirements-rpm.txt)
CENTOSRPMFORGE_PACKAGES:=qemu

ifdef MIRROR_DIR
CENTOS_REPO_DIR:=$(MIRROR_DIR)/centos/
else
CENTOS_REPO_DIR:=$/
endif


# RPM PACKAGE CACHE RULES

ifeq ($(IGNORE_MIRROR),1)
REPO_SUFFIX=real
else
REPO_SUFFIX=mirror
endif

define yum_conf
[main]
cachedir=$(CENTOS_REPO_DIR)cache
keepcache=0
debuglevel=6
logfile=$(CENTOS_REPO_DIR)yum.log
exactarch=1
obsoletes=1
gpgcheck=0
plugins=0
reposdir=$(CENTOS_REPO_DIR)etc/yum-$(REPO_SUFFIX).repos.d
endef

$(CENTOS_REPO_DIR)etc/yum-$(REPO_SUFFIX).conf: export contents:=$(yum_conf)
$(CENTOS_REPO_DIR)etc/yum-$(REPO_SUFFIX).conf:
	@mkdir -p $(@D)
	echo "$${contents}" > $@

define yum_mirror_repo
[mirror]
name=CentOS $(CENTOS_63_RELEASE) - Base
baseurl=$(REPOMIRROR)/Packages
gpgcheck=0
enabled=1
endef

define yum_real_repo
[base]
name=CentOS-$(CENTOS_63_RELEASE) - Base
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_63_RELEASE)&arch=$(CENTOS_63_ARCH)&repo=os
baseurl=$(CENTOSMIRROR)/$(CENTOS_63_RELEASE)/os/$(CENTOS_63_ARCH)
gpgcheck=0
enabled=1

[updates]
name=CentOS-$(CENTOS_63_RELEASE) - Updates
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_63_RELEASE)&arch=$(CENTOS_63_ARCH)&repo=updates
baseurl=$(CENTOSMIRROR)/$(CENTOS_63_RELEASE)/updates/$(CENTOS_63_ARCH)
gpgcheck=0
enabled=1

[extras]
name=CentOS-$(CENTOS_63_RELEASE) - Extras
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_63_RELEASE)&arch=$(CENTOS_63_ARCH)&repo=extras
baseurl=$(CENTOSMIRROR)/$(CENTOS_63_RELEASE)/extras/$(CENTOS_63_ARCH)
gpgcheck=0
enabled=1

[centosplus]
name=CentOS-$(CENTOS_63_RELEASE) - Plus
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_63_RELEASE)&arch=$(CENTOS_63_ARCH)&repo=centosplus
baseurl=$(CENTOSMIRROR)/$(CENTOS_63_RELEASE)/centosplus/$(CENTOS_63_ARCH)
gpgcheck=0
enabled=1

[contrib]
name=CentOS-$(CENTOS_63_RELEASE) - Contrib
#mirrorlist=http://mirrorlist.centos.org/?release=$(CENTOS_63_RELEASE)&arch=$(CENTOS_63_ARCH)&repo=contrib
baseurl=$(CENTOSMIRROR)/$(CENTOS_63_RELEASE)/contrib/$(CENTOS_63_ARCH)
gpgcheck=0
enabled=1

[epel]
name=Extra Packages for Enterprise Linux $(CENTOS_63_MAJOR) - $(CENTOS_63_ARCH)
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-$(CENTOS_63_MAJOR)&arch=$(CENTOS_63_ARCH)
baseurl=$(EPELMIRROR)/$(CENTOS_63_MAJOR)/$(CENTOS_63_ARCH)
gpgcheck=0
enabled=1

[mirantis]
name=Mirantis Packages for CentOS
baseurl=http://moc-ci.srt.mirantis.net/rpm
gpgcheck=0
enabled=0

[rpmforge]
name=RHEL $(CENTOS_63_RELEASE) - RPMforge.net - dag
#mirrorlist = http://apt.sw.be/redhat/el6/en/mirrors-rpmforge
baseurl=$(RPMFORGEMIRROR)/el$(CENTOS_63_MAJOR)/en/$(CENTOS_63_ARCH)/rpmforge
gpgcheck=0
enabled=0

[rpmforge-extras]
name = RHEL $(CENTOS_63_RELEASE) - RPMforge.net - extras
#mirrorlist = http://apt.sw.be/redhat/el6/en/mirrors-rpmforge-extras
baseurl = $(RPMFORGEMIRROR)/el$(CENTOS_63_MAJOR)/en/$(CENTOS_63_ARCH)/extras
gpgcheck = 0
enabled = 0
endef

$(CENTOS_REPO_DIR)etc/yum-$(REPO_SUFFIX).repos.d/base.repo: export contents:=$(yum_$(REPO_SUFFIX)_repo)

$(CENTOS_REPO_DIR)etc/yum-$(REPO_SUFFIX).repos.d/base.repo:
	@mkdir -p $(@D)
	echo "$${contents}" > $@

### NOTE: comps.xml came from centos-minimal.iso
$(CENTOS_REPO_DIR)comps.xml: os/centos/comps.xml
	$(ACTION.COPY)

$(CENTOS_REPO_DIR)cache-infra.done: \
	  $(CENTOS_REPO_DIR)etc/yum-$(REPO_SUFFIX).conf \
	  $(CENTOS_REPO_DIR)etc/yum-$(REPO_SUFFIX).repos.d/base.repo
	$(ACTION.TOUCH)

$(CENTOS_REPO_DIR)cache-extra.done: \
	  $(CENTOS_REPO_DIR)cache-infra.done
	yum -c $(CENTOS_REPO_DIR)etc/yum-$(REPO_SUFFIX).conf clean all
	rm -rf /var/tmp/yum-$$USER-*/
ifeq ($(IGNORE_MIRROR),1)
	repotrack -c $(CENTOS_REPO_DIR)etc/yum-$(REPO_SUFFIX).conf -p $(CENTOS_REPO_DIR)Packages -a $(CENTOS_63_ARCH) $(CENTOSMIN_PACKAGES) $(CENTOSEXTRA_PACKAGES)
	repotrack -r base -r updates -r extras -r contrib -r centosplus -r epel -r rpmforge-extras -c $(CENTOS_REPO_DIR)etc/yum-$(REPO_SUFFIX).conf -p $(CENTOS_REPO_DIR)Packages -a $(CENTOS_63_ARCH) $(CENTOSRPMFORGE_PACKAGES)
	### NOTE: qemu-img-0.15 conflicts with packages in epel repos
	-rm $(CENTOS_REPO_DIR)Packages/qemu-img-0.15*
else
	repotrack -c $(CENTOS_REPO_DIR)etc/yum-$(REPO_SUFFIX).conf -p $(CENTOS_REPO_DIR)Packages -a $(CENTOS_63_ARCH) $(CENTOSMIN_PACKAGES) $(CENTOSEXTRA_PACKAGES) $(CENTOSRPMFORGE_PACKAGES)
endif
	$(ACTION.TOUCH)

$(CENTOS_REPO_DIR)cache.done: $(CENTOS_REPO_DIR)cache-extra.done $(CENTOS_REPO_DIR)comps.xml
	$(ACTION.TOUCH)

METADATA_FILES=repomd.xml comps.xml filelists.xml.gz primary.xml.gz other.xml.gz
$(addprefix $(CENTOS_REPO_DIR)Packages/repodata/,$(METADATA_FILES)): $(CENTOS_REPO_DIR)cache.done
	createrepo -g `readlink -f "$(CENTOS_REPO_DIR)comps.xml"` -o $(CENTOS_REPO_DIR)Packages $(CENTOS_REPO_DIR)Packages

$(CENTOS_REPO_DIR)repo.done: $(addprefix $(CENTOS_REPO_DIR)Packages/repodata/,$(METADATA_FILES))
	touch $@

mirror: $(addprefix $(CENTOS_REPO_DIR)Packages/repodata/,$(METADATA_FILES))