/:=$(BUILD_DIR)/packages/centos/

$/%: /:=$/

CENTOSMIRROR:=http://mirror.san.fastserv.com/pub/linux/centos

CENTOSEXTRA_PACKAGES:=$(shell grep -v ^\\s*\# requirements-rpm.txt)

# RPM PACKAGE CACHE RULES

define yum_conf
[main]
cachedir=$/cache
keepcache=0
debuglevel=6
logfile=$/yum.log
exactarch=1
obsoletes=1
gpgcheck=0
plugins=0
reposdir=$/etc/yum.repos.d
endef

$/etc/yum.conf: export contents:=$(yum_conf)
$/etc/yum.conf: | $/etc/.dir
	@mkdir -p $(@D)
	echo "$${contents}" > $@

define yum_base_repo
[base]
name=CentOS $(CENTOS_62_RELEASE) - Base
baseurl=$(CENTOSMIRROR)/$(CENTOS_62_RELEASE)/os/$(CENTOS_62_ARCH)
gpgcheck=0
enabled=1

[updates]
name=CentOS $(CENTOS_62_RELEASE) - Updates
baseurl=$(CENTOSMIRROR)/$(CENTOS_62_RELEASE)/updates/$(CENTOS_62_ARCH)
gpgcheck=0
enabled=1

[extras]
name=CentOS $(CENTOS_62_RELEASE) - Extras
baseurl=$(CENTOSMIRROR)/$(CENTOS_62_RELEASE)/extras/$(CENTOS_62_ARCH)
gpgcheck=0
enabled=1

[centosplus]
name=CentOS $(CENTOS_62_RELEASE) - Plus
baseurl=$(CENTOSMIRROR)/$(CENTOS_62_RELEASE)/centosplus/$(CENTOS_62_ARCH)
gpgcheck=0
enabled=1

[contrib]
name=CentOS $(CENTOS_62_RELEASE) - Contrib
baseurl=$(CENTOSMIRROR)/$(CENTOS_62_RELEASE)/contrib/$(CENTOS_62_ARCH)
gpgcheck=0
enabled=1

[epel]
name=Extra Packages for Enterprise Linux 6
baseurl=http://download.fedoraproject.org/pub/epel/$(CENTOS_62_MAJOR)/$(CENTOS_62_ARCH)
enabled=1
gpgcheck=0

[mirantis]
name=Mirantis Packages for CentOS
baseurl=http://moc-ci.srt.mirantis.net/rpm
enabled=1
gpgcheck=0
endef

$/etc/yum.repos.d/base.repo: export contents:=$(yum_base_repo)
$/etc/yum.repos.d/base.repo: | $/etc/yum.repos.d/.dir
	@mkdir -p $(@D)
	echo "$${contents}" > $@

$/comps.xml: $(BINARIES_DIR)/centos/$(CENTOS_62_RELEASE)/comps.xml
	$(ACTION.COPY)

$/cache-infra.done: \
	  $/etc/yum.conf \
	  $/etc/yum.repos.d/base.repo
	$(ACTION.TOUCH)

$/cache-iso.done: $(CENTOS_62_ISO) | $(CENTOS_62_ROOT)/Packages $/Packages/.dir
	find $(abspath $(CENTOS_62_ROOT)/Packages) -type f \( -name '*.rpm' \) -exec ln -sf {} $/Packages \;
	$(ACTION.TOUCH)

$/cache-extra.done: \
	  $/cache-infra.done \
	  $/cache-iso.done \
	  $(addprefix $/Packages/,$(call find-files,$(BINARIES_DIR)/centos/$(CENTOS_62_RELEASE)/Packages)) \
	  requirements-rpm.txt
	for p in $(CENTOSEXTRA_PACKAGES); do \
	repotrack -c $/etc/yum.conf -p $/Packages -a $(CENTOS_62_ARCH) $$p; \
	done
	$(ACTION.TOUCH)

$/Packages/%.rpm: $(BINARIES_DIR)/centos/$(CENTOS_62_RELEASE)/Packages/%.rpm
	ln -sf $(abspath $<) $@

$/cache.done: $/cache-extra.done $/comps.xml
	$(ACTION.TOUCH)

METADATA_FILES=repomd.xml comps.xml filelists.xml.gz primary.xml.gz other.xml.gz
$(addprefix $(BUILD_DIR)/packages/%/Packages/repodata/,$(METADATA_FILES)): $/cache.done
	createrepo -g `readlink -f "$/comps.xml"` -o $(BUILD_DIR)/packages/$*/Packages $(BUILD_DIR)/packages/$*/Packages

$/repo.done: $(addprefix $/Packages/repodata/,$(METADATA_FILES))
	$(ACTION.TOUCH)

