extra_centos_empty_installroot:=$(BUILD_DIR)/mirror/centos/dummy_extra_installroot

define yum_cr_repo
name=CentOS-$(CENTOS_RELEASE) CR repo
baseurl=$(MIRROR_CENTOS)/cr/$(CENTOS_ARCH)
gpgcheck=0
enabled=1
priority=21
exclude=*i686 $(x86_rpm_packages_whitelist) *debuginfo*
endef

export cr_repo_config=$(call yum_cr_repo)

$(BUILD_DIR)/mirror/centos/cr-repo-download.done:
	mkdir -p $(LOCAL_MIRROR)/centos/cr/$(CENTOS_ARCH)
	mkdir -p "$(extra_centos_empty_installroot)/cache"
	set -ex; env TMPDIR="$(extra_centos_empty_installroot)/cache" \
		TMP="$(extra_centos_empty_installroot)/cache" \
		reposync --downloadcomps --plugins --delete --arch=$(CENTOS_ARCH) \
		--cachedir="$(extra_centos_empty_installroot)/cache" \
		-c $(BUILD_DIR)/mirror/centos/etc/yum.conf --repoid=cr \
		-p $(LOCAL_MIRROR)/centos/cr/$(CENTOS_ARCH) --norepopath
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/centos/cr.repo:
	mkdir -p $(@D)
	/bin/echo -e "$${cr_repo_config}" > $@

ifeq ($(CENTOS_USE_CR),none)
$(BUILD_DIR)/mirror/centos/cr-repo.done:
	$(ACTION.TOUCH)
else
$(BUILD_DIR)/mirror/centos/cr-repo.done: $(BUILD_DIR)/mirror/centos/cr-repo-download.done
$(BUILD_DIR)/mirror/centos/cr-repo.done: $(BUILD_DIR)/mirror/centos/cr.repo
$(BUILD_DIR)/mirror/centos/cr-repo.done:
	createrepo -o $(LOCAL_MIRROR)/centos/cr/$(CENTOS_ARCH) $(LOCAL_MIRROR)/centos/cr/$(CENTOS_ARCH)
	$(ACTION.TOUCH)
endif
