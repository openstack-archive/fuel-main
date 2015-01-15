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
	mkdir -p $(centos_empty_installroot)
	yum --installroot=$(centos_empty_installroot) -c $< makecache
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/centos/yum.done: $(BUILD_DIR)/mirror/centos/rpm-download.done
	$(ACTION.TOUCH)

ifneq (,$(strip $(YUM_DOWNLOAD_SRC)))
$(BUILD_DIR)/mirror/centos/yum.done: $(BUILD_DIR)/mirror/centos/src-rpm-download.done
endif

$(BUILD_DIR)/mirror/centos/rpm-download.done: $(BUILD_DIR)/mirror/centos/urls.list
	dst="$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages"; \
	mkdir -p "$$dst" && \
	xargs -n1 -P4 wget -nv -P "$$dst" < $< 
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/centos/src-rpm-download.done: $(BUILD_DIR)/mirror/centos/src_urls.list
	dst="$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Sources"; \
	mkdir -p "$$dst" && \
	xargs -n1 -P4 wget -nv -P "$$dst" < $<
	$(ACTION.TOUCH)

rpm_download_lists:=$(REQUIRED_RPMS:%=$(BUILD_DIR)/mirror/centos/lists/%.list)
src_rpm_download_lists:=$(REQUIRED_RPMS:%=$(BUILD_DIR)/mirror/centos/src_lists/%.list)

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

$(BUILD_DIR)/mirror/centos/src_urls.list: $(src_rpm_download_lists)
	mkdir -p $(@D) && \
	cat $^ > $@.pre
# yumdownloader -q prints logs to stdout, filter them out
	sed -rne '/\.rpm$$/ {p}' -i $@.pre && \
	sort -u < $@.pre > $@.tmp && \
	mv $@.tmp $@

# XXX: yumdownloader operates upon rpmdb so running several instances
# concurrently (within the same installroot) is not safe. Create
# an installroot template and make a copy for every yumdownloader process
# (each installroot is about 200Kb, so copying is not a problem)
# others' feet)

$(rpm_download_lists): $(BUILD_DIR)/mirror/centos/lists/%.list: \
		$(BUILD_DIR)/mirror/centos/yum-config.done \
		$(SOURCE_DIR)/requirements-rpm.txt
	tmp_installchroot=$(dir $(centos_empty_installroot))installchroot-$*; \
	cp -a "$(centos_empty_installroot)" "$$tmp_installchroot" && \
	mkdir -p $(@D) && \
	yumdownloader -q --urls \
		--archlist=$(CENTOS_ARCH) \
		--installroot="$$tmp_installchroot" \
		-c $(BUILD_DIR)/mirror/centos/etc/yum.conf \
		--cacheonly \
		--resolve $* > $@.tmp 2>$@.log && \
	rm -rf "$$tmp_installchroot" && \
	mv $@.tmp $@

$(src_rpm_download_lists): $(BUILD_DIR)/mirror/centos/src_lists/%.list: \
		$(BUILD_DIR)/mirror/centos/yum-config.done \
		$(SOURCE_DIR)/requirements-rpm.txt
	tmp_installchroot=$(dir $(centos_empty_installroot))installchroot-src-$*; \
	cp -a "$(centos_empty_installroot)" "$$tmp_installchroot" && \
	mkdir -p $(@D) && \
	yumdownloader -q --urls \
		--archlist=src --source \
		--installroot="$$tmp_installchroot" \
		-c $(BUILD_DIR)/mirror/centos/etc/yum.conf \
		--cacheonly \
		--resolve $* > $@.tmp 2>$@.log && \
	rm -rf "$$tmp_installchroot" && \
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
