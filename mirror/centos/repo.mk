include $(SOURCE_DIR)/mirror/centos/config.mk
include $(SOURCE_DIR)/mirror/centos/config_yum.mk

$(BUILD_DIR)/mirror/centos/etc/yum.conf: export contents:=$(yum_conf)
$(BUILD_DIR)/mirror/centos/etc/yum.conf: \
		$(SOURCE_DIR)/mirror/centos/yum-priorities-plugin.py
	mkdir -p $(BUILD_DIR)/mirror/centos/etc/yum/pluginconf.d
	echo "[main]\nenabled=1" > $(BUILD_DIR)/mirror/centos/etc/yum/pluginconf.d/priorities.conf
	mkdir -p $(BUILD_DIR)/mirror/centos/etc/yum-plugins
	cp $(SOURCE_DIR)/mirror/centos/yum-priorities-plugin.py $(BUILD_DIR)/mirror/centos/etc/yum-plugins/priorities.py
	mkdir -p $(@D)
	echo "$${contents}" > $@


$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/base.repo: \
		export contents:=$(foreach repo,$(YUM_REPOS),\n$(yum_repo_$(repo)))
$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/base.repo: \
		$(SOURCE_DIR)/mirror/centos/config.mk
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
		$(REQUIRED_PACKAGES) $(RPMFORGE_PACKAGES)
	$(ACTION.TOUCH)

$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/repodata/comps.xml:
	@mkdir -p $(@D)
	wget -O $@.gz $(CENTOS_MIRROR_OS_BASEURL)/`wget -qO- $(CENTOS_MIRROR_OS_BASEURL)/repodata/repomd.xml | \
	 grep '$(@F)\.gz' | awk -F'"' '{ print $$2 }'`
	gunzip $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/repodata/$(@F).gz

$(BUILD_DIR)/mirror/centos/repo.done: \
		$(BUILD_DIR)/mirror/centos/yum.done \
		| $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/repodata/comps.xml
	createrepo -g `readlink -f "$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/repodata/comps.xml"` \
		-o $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/ $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/
	$(ACTION.TOUCH)
