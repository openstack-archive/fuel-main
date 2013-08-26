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

$(BUILD_DIR)/mirror/centos/yum-config.done: \
		$(BUILD_DIR)/mirror/centos/etc/yum.conf \
		$(BUILD_DIR)/mirror/centos/etc/yum.repos.d/base.repo \
		$(BUILD_DIR)/mirror/centos/etc/yum-plugins/priorities.py \
		$(BUILD_DIR)/mirror/centos/etc/yum/pluginconf.d/priorities.conf
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/centos/yum.done: \
		$(BUILD_DIR)/mirror/centos/yum-config.done \
		$(SOURCE_DIR)/requirements-rpm.txt
	yum -c $(BUILD_DIR)/mirror/centos/etc/yum.conf clean all
	rm -rf /var/tmp/yum-$$USER-*/
	yumdownloader -q --resolve --archlist=$(CENTOS_ARCH) \
		-c $(BUILD_DIR)/mirror/centos/etc/yum.conf \
		--destdir=$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \
		$(REQUIRED_RPMS)
	$(ACTION.TOUCH)

show-yum-urls-centos: \
		$(BUILD_DIR)/mirror/centos/yum-config.done \
		$(SOURCE_DIR)/requirements-rpm.txt
	yum -c $(BUILD_DIR)/mirror/centos/etc/yum.conf clean all
	rm -rf /var/tmp/yum-$$USER-*/
	yumdownloader --urls -q --resolve --archlist=$(CENTOS_ARCH) \
		-c $(BUILD_DIR)/mirror/centos/etc/yum.conf \
		--destdir=$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages \
		$(REQUIRED_RPMS)

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
