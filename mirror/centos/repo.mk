define yum_conf
[main]
cachedir=$(BUILD_DIR)/mirror/centos/cache
keepcache=0
debuglevel=6
logfile=$(BUILD_DIR)/mirror/centos/yum.log
exclude=*.i686.rpm ntp-dev*
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
pluginpath=$(BUILD_DIR)/mirror/centos/etc/yum-plugins
pluginconfpath=$(BUILD_DIR)/mirror/centos/etc/yum/pluginconf.d
reposdir=$(BUILD_DIR)/mirror/centos/etc/yum.repos.d
endef

# It's a callable object.
# Usage: $(call create_repo,repo)
# where:
# repo=repo_name,repo_priority,http://path_to_the_repo
# repo_priority is a number from 1 to 99
define create_repo
[$(shell echo $($1) | cut -d ',' -f 1)]
name = Repo "$(shell echo $($1) | cut -d ',' -f 1)"
baseurl = $(shell echo $($1) | cut -d ',' -f 3)
gpgcheck = 0
enabled = 1
priority = $(shell echo $($1) | cut -d ',' -f 2)
endef

# First repository is used to download comps.xml files.
MIRROR_CENTOS_OS_BASEURL?=$(shell echo $(firstword $(MULTI_MIRROR_CENTOS)) | cut -d ',' -f 3)

.PHONY: show-yum-urls-centos

$(BUILD_DIR)/mirror/centos/etc/yum.conf: $(call depv,yum_conf)
$(BUILD_DIR)/mirror/centos/etc/yum.conf: export contents:=$(yum_conf)
$(BUILD_DIR)/mirror/centos/etc/yum.conf:
	mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

$(BUILD_DIR)/mirror/centos/etc/yum-plugins/priorities.py: \
		$(SOURCE_DIR)/mirror/centos/yum-priorities-plugin.py
	mkdir -p $(@D)
	cp $(SOURCE_DIR)/mirror/centos/yum-priorities-plugin.py $@

$(BUILD_DIR)/mirror/centos/etc/yum/pluginconf.d/priorities.conf:
	mkdir -p $(@D)
	/bin/echo -e "[main]\nenabled=1\ncheck_obsoletes=1\nfull_match=1" > $@

$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/all.repo: $(call depv,MULTI_MIRROR_CENTOS)
$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/all.repo: \
		export contents:=$(foreach repo,$(MULTI_MIRROR_CENTOS),$(NEWLINE)$(call create_repo,repo)$(NEWLINE))
$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/all.repo:
	@mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

centos_empty_installroot:=$(BUILD_DIR)/mirror/centos/dummy_installroot

$(BUILD_DIR)/mirror/centos/yum-config.done: \
		$(BUILD_DIR)/mirror/centos/etc/yum.conf \
		$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/all.repo \
		$(BUILD_DIR)/mirror/centos/etc/yum-plugins/priorities.py \
		$(BUILD_DIR)/mirror/centos/etc/yum/pluginconf.d/priorities.conf
	rm -rf $(centos_empty_installroot)
	mkdir -p $(centos_empty_installroot)/cache
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/centos/yum.done: $(BUILD_DIR)/mirror/centos/rpm-download.done
	$(ACTION.TOUCH)

ifneq (,$(strip $(YUM_DOWNLOAD_SRC)))
$(BUILD_DIR)/mirror/centos/yum.done: $(BUILD_DIR)/mirror/centos/src-rpm-download.done
endif

$(BUILD_DIR)/mirror/centos/rpm-download.done: $(BUILD_DIR)/mirror/centos/urls.list
	dst="$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages"; \
	mkdir -p "$$dst" && \
	xargs -n1 -P4 wget -Nnv -P "$$dst" < $<
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/centos/src-rpm-download.done: $(BUILD_DIR)/mirror/centos/src_urls.list
	dst="$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Sources"; \
	mkdir -p "$$dst" && \
	xargs --no-run-if-empty -n1 -P4 wget -Nnv -P "$$dst" < $<
	$(ACTION.TOUCH)


$(BUILD_DIR)/mirror/centos/urls.list: $(SOURCE_DIR)/requirements-rpm.txt \
		$(BUILD_DIR)/mirror/centos/yum-config.done
	mkdir -p $(@D) && \
	env \
		TMPDIR="$(centos_empty_installroot)/cache" \
		TMP="$(centos_empty_installroot)/cache" \
	yumdownloader -q --urls \
		--archlist=$(CENTOS_ARCH) \
		--installroot="$(centos_empty_installroot)" \
		-c $(BUILD_DIR)/mirror/centos/etc/yum.conf \
		--resolve \
		`cat $(SOURCE_DIR)/requirements-rpm.txt` > "$@.out" 2>"$@.log"
	# yumdownloader -q prints logs to stdout, filter them out
	sed -rne '/\.rpm$$/ {p}' < $@.out > $@.pre
# yumdownloader selects i686 packages too. Remove them. However be
# careful not to remove the syslinux-nolinux package (it contains
# 32 binaries executed on a bare hardware. That package really should
# have been noarch
	sed -re '/i686\.rpm$$/ { /syslinux-nonlinux/p;d }' -i $@.pre
	sort -u < $@.pre > $@.tmp
	mv $@.tmp $@

$(BUILD_DIR)/mirror/centos/mirantis_rpms.list: $(BUILD_DIR)/mirror/centos/urls.list
	sed -rne '/$(subst /,\/,$(MIRROR_FUEL))/ s/^.*[/]([^/]+)\.($(CENTOS_ARCH)|noarch)\.rpm$$/\1/p' < $< > $@.pre && \
	sort -u < $@.pre > $@.tmp && \
	mv $@.tmp $@

$(BUILD_DIR)/mirror/centos/src_urls.list: $(BUILD_DIR)/mirror/centos/mirantis_rpms.list
	mkdir -p "$(@D)" && \
	env \
		TMPDIR="$(centos_empty_installroot)/cache" \
		TMP="$(centos_empty_installroot)/cache" \
	yumdownloader -q --urls \
		--archlist=src --source \
		--installroot="$(centos_empty_installroot)" \
		-c $(BUILD_DIR)/mirror/centos/etc/yum.conf \
		--cacheonly \
		`cat $<` > $@.pre 2>$@.log
	sed -rne '/\.rpm$$/ {p}' -i $@.pre && \
	sort -u < $@.pre > $@.tmp && \
	mv $@.tmp $@

show-yum-urls-centos: $(BUILD_DIR)/mirror/centos/urls.list
	cat $<

$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml: \
		export COMPSXML=$(shell wget -qO- $(MIRROR_CENTOS_OS_BASEURL)/repodata/repomd.xml | grep -m 1 '$(@F)' | awk -F'"' '{ print $$2 }')
$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml:
	@mkdir -p $(@D)
	if ( echo $${COMPSXML} | grep -q '\.gz$$' ); then \
		wget -O $@.gz $(MIRROR_CENTOS_OS_BASEURL)/$${COMPSXML}; \
		gunzip $@.gz; \
	else \
		wget -O $@ $(MIRROR_CENTOS_OS_BASEURL)/$${COMPSXML}; \
	fi

$(BUILD_DIR)/mirror/centos/repo.done: \
		$(BUILD_DIR)/mirror/centos/yum.done \
		| $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml
	createrepo -g $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/ $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/
	$(ACTION.TOUCH)
