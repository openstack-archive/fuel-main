include $(SOURCE_DIR)/mirror/centos/yum_repos.mk

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

$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/base.repo: $(call depv,YUM_REPOS)
$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/base.repo: \
		export contents:=$(foreach repo,$(YUM_REPOS),\n$(yum_repo_$(repo))\n)
$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/base.repo:
	@mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/extra.repo: $(call depv,EXTRA_RPM_REPOS)
$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/extra.repo: \
		export contents:=$(foreach repo,$(EXTRA_RPM_REPOS),\n$(call create_extra_repo,repo)\n)
$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/extra.repo:
	@mkdir -p $(@D)
	/bin/echo -e "$${contents}" > $@

centos_empty_installroot:=$(BUILD_DIR)/mirror/centos/dummy_installroot

$(BUILD_DIR)/mirror/centos/yum-config.done: \
		$(BUILD_DIR)/mirror/centos/etc/yum.conf \
		$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/base.repo \
		$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/extra.repo \
		$(BUILD_DIR)/mirror/centos/etc/yum-plugins/priorities.py \
		$(BUILD_DIR)/mirror/centos/etc/yum/pluginconf.d/priorities.conf
	rm -rf $(centos_empty_installroot)
	mkdir -p $(centos_empty_installroot)/cache
# By default yum uses /var/tmp/yum-$USER-xxyyzz as a meta-data cache. Use
# a local directory to avoid old meta-data copies. Also makes it possible
# to run several builds in parallel
	env \
		TMPDIR='$(centos_empty_installroot)/cache' \
		TMP='$(centos_empty_installroot)/cahce' \
		yum --installroot=$(centos_empty_installroot) -c $< makecache
# yum makecache does not load groups lists data, run some command which makes
# use of group lists (and downloads them as a side effect)
	env \
		TMPDIR='$(centos_empty_installroot)/cache' \
		TMP='$(centos_empty_installroot)/cahce' \
	yumdownloader -q --urls \
		--archlist=$(CENTOS_ARCH) \
		--installroot="$(centos_empty_installroot)" \
		-c $< --resolve @Base @Core > /dev/null
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/centos/yum.done: $(BUILD_DIR)/mirror/centos/rpm-download.done
	$(ACTION.TOUCH)

ifneq (,$(strip $(YUM_DOWNLOAD_SRC)))
$(BUILD_DIR)/mirror/centos/yum.done: $(BUILD_DIR)/mirror/centos/src-rpm-download.done
endif

$(BUILD_DIR)/mirror/centos/rpm-download.done: $(BUILD_DIR)/mirror/centos/urls.list
	dst="$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages"; \
	mkdir -p "$$dst" && \
	xargs -n1 -P4 wget -r -nv -P "$$dst" < $< 
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/centos/src-rpm-download.done: $(BUILD_DIR)/mirror/centos/src_urls.list
	dst="$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Sources"; \
	mkdir -p "$$dst" && \
	xargs --no-run-if-empty -n1 -P4 wget -r -nv -P "$$dst" < $<
	$(ACTION.TOUCH)

rpm_download_lists:=$(REQUIRED_RPMS:%=$(BUILD_DIR)/mirror/centos/lists/%.list)
mirantis_rpms_list:=$(BUILD_DIR)/mirror/centos/mirantis_rpms.list

$(BUILD_DIR)/mirror/centos/urls.list: $(rpm_download_lists)
	mkdir -p $(@D)
	cat $^ > $@.pre
	# yumdownloader -q prints logs to stdout, filter them out
	sed -rne '/\.rpm$$/ {p}' -i $@.pre
# yumdownloader selects i686 packages too. Remove them. However be
# careful not to remove the syslinux-nolinux package (it contains
# 32 binaries executed on a bare hardware. That package really should
# have been noarch
	sed -re '/i686\.rpm$$/ { /syslinux-nonlinux/p;d }' -i $@.pre
	sort -u < $@.pre > $@.tmp
	mv $@.tmp $@


# XXX: yumdownloader operates upon rpmdb so running several instances
# concurrently (within the same installroot) is not safe. Create
# an installroot template and make a shallow copy for every yumdownloader
# process. Hard link the repository metadata too and tell yum to use that
# (instead of /var/tmp/yum-$USER-xxyyzz) via TMP and TMPDIR environment
# variables.

$(rpm_download_lists): $(BUILD_DIR)/mirror/centos/lists/%.list: \
		$(BUILD_DIR)/mirror/centos/yum-config.done \
		$(SOURCE_DIR)/requirements-rpm.txt
	tmp_installchroot=$(dir $(centos_empty_installroot))installchroot-$*; \
	cp -al "$(centos_empty_installroot)" "$$tmp_installchroot" && \
	mkdir -p $(@D) && \
	env \
		TMPDIR="$$tmp_installchroot/cache" \
		TMP="$$tmp_installchroot/cache" \
	yumdownloader -q --urls \
		--archlist=$(CENTOS_ARCH) \
		--installroot="$$tmp_installchroot" \
		-c $(BUILD_DIR)/mirror/centos/etc/yum.conf \
		--cacheonly \
		--resolve $* > $@.tmp 2>$@.log && \
	rm -rf "$$tmp_installchroot" && \
	mv $@.tmp $@


$(BUILD_DIR)/mirantis_rpm_pkgs_list.mk: $(BUILD_DIR)/mirror/centos/urls.list
	sed -rne '/$(subst /,\/,$(MIRROR_FUEL))/ s/^.*[/]([^/]+)\.($(CENTOS_ARCH)|noarch)\.rpm$$/\1\\/p' < $< > $@.pre.list
	sort -u < $@.pre.list > $@.list && \
	echo 'mirantis_rpm_pkgs_list:=\\' > $@.tmp && \
	cat $@.list >> $@.tmp && \
	echo '$$(empty)' >> $@.tmp && \
	mv $@.tmp $@

ifneq (,$(strip $(YUM_DOWNLOAD_SRC)))
ifeq (,$(findstring clean,$(MAKECMDGOALS)))
include $(BUILD_DIR)/mirantis_rpm_pkgs_list.mk
endif

mirantis_src_rpm_urls_list:=$(mirantis_rpm_pkgs_list:%=$(BUILD_DIR)/mirror/centos/src_lists/%.list)

$(mirantis_src_rpm_urls_list): $(BUILD_DIR)/mirror/centos/src_lists/%.list: \
		$(BUILD_DIR)/mirror/centos/yum-config.done \
		$(SOURCE_DIR)/requirements-rpm.txt
	tmp_installchroot=$(dir $(centos_empty_installroot))installchroot-src-$*; \
	cp -al "$(centos_empty_installroot)" "$$tmp_installchroot" && \
	mkdir -p "$(@D)" && \
	env \
		TMPDIR="$$tmp_installchroot/cache" \
		TMP="$$tmp_installchroot/cache" \
	yumdownloader -q --urls \
		--archlist=src --source \
		--installroot="$$tmp_installchroot" \
		-c $(BUILD_DIR)/mirror/centos/etc/yum.conf \
		--cacheonly \
		 $* > $@.tmp 2>$@.log && \
	rm -rf "$$tmp_installchroot" && \
	mv $@.tmp $@

$(BUILD_DIR)/mirror/centos/src_urls.list: $(mirantis_src_rpm_urls_list)
	mkdir -p "$(@D)" && \
	cat $^ > $@.pre && \
	sed -rne '/\.rpm$$/ {p}' -i $@.pre && \
	sort -u $@.pre > $@.tmp && \
	mv $@.tmp $@

endif
# YUM_DOWNLOAD_SRC

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
