include $(SOURCE_DIR)/mirror/centos/yum_repos.mk

$(BUILD_DIR)/mirror/centos/etc/yum.conf: $(call depv,yum_conf)
$(BUILD_DIR)/mirror/centos/etc/yum.conf: export contents:=$(yum_conf)
$(BUILD_DIR)/mirror/centos/etc/yum.conf: \
		$(SOURCE_DIR)/mirror/centos/yum_repos.mk \
		$(SOURCE_DIR)/mirror/centos/yum-priorities-plugin.py
	mkdir -p $(BUILD_DIR)/mirror/centos/etc/yum/pluginconf.d
	echo "[main]\nenabled=1" > $(BUILD_DIR)/mirror/centos/etc/yum/pluginconf.d/priorities.conf
	mkdir -p $(BUILD_DIR)/mirror/centos/etc/yum-plugins
	cp $(SOURCE_DIR)/mirror/centos/yum-priorities-plugin.py $(BUILD_DIR)/mirror/centos/etc/yum-plugins/priorities.py
	mkdir -p $(@D)
	echo "$${contents}" > $@


$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/base.repo: $(call depv,YUM_REPOS)
$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/base.repo: \
		export contents:=$(foreach repo,$(YUM_REPOS),\n$(yum_repo_$(repo)))
$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/base.repo: \
		$(SOURCE_DIR)/mirror/centos/yum_repos.mk
	@mkdir -p $(@D)
	echo "$${contents}" > $@

$(BUILD_DIR)/mirror/centos/yum-config.done: \
		$(BUILD_DIR)/mirror/centos/etc/yum.conf \
		$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/base.repo
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/centos/yum.done: \
		$(BUILD_DIR)/mirror/centos/yum-config.done \
		$(SOURCE_DIR)/requirements-rpm.txt
	yum -c $(BUILD_DIR)/mirror/centos/etc/yum.conf clean all
	rm -rf /var/tmp/yum-$$USER-*/
	yumdownloader -q --resolve --archlist=$(CENTOS_ARCH) \
		-c $(BUILD_DIR)/mirror/centos/etc/yum.conf \
		--destdir=$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \
		$(REQUIRED_RPMS) $(RPMFORGE_RPMS)
	$(ACTION.TOUCH)

$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/repodata/comps.xml:
	@mkdir -p $(@D)
	wget -O $@.gz $(MIRROR_CENTOS_OS_BASEURL)/`wget -qO- $(MIRROR_CENTOS_OS_BASEURL)/repodata/repomd.xml | \
	 grep '$(@F)\.gz' | awk -F'"' '{ print $$2 }'`
	gunzip $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/repodata/$(@F).gz

$(BUILD_DIR)/mirror/centos/repo.done: \
		$(BUILD_DIR)/mirror/centos/yum.done \
		| $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/repodata/comps.xml
	createrepo -g `readlink -f "$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/repodata/comps.xml"` \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/ $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/
	$(ACTION.TOUCH)
