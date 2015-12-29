extra_centos_empty_installroot:=$(BUILD_DIR)/mirror/centos/dummy_extra_installroot

$(BUILD_DIR)/mirror/centos/extra-repos-download.done: $(BUILD_DIR)/mirror/centos/yum-config.done
$(BUILD_DIR)/mirror/centos/extra-repos-download.done:
	mkdir -p $(LOCAL_MIRROR)/extra-repos
	$(foreach repo,$(EXTRA_RPM_REPOS),$(call extra_repo_download,$(repo));)
	$(ACTION.TOUCH)

$(LOCAL_MIRROR)/extra-repos/extra.repo: $(call depv,EXTRA_RPM_REPOS)
$(LOCAL_MIRROR)/extra-repos/extra.repo: \
		export fuelnode_repos:=$(foreach repo,$(EXTRA_RPM_REPOS),\n$(call create_fuelnode_repo,$(repo))\n)
$(LOCAL_MIRROR)/extra-repos/extra.repo:
	mkdir -p $(@D)
	/bin/echo -e "$${fuelnode_repos}" > $@

$(BUILD_DIR)/mirror/centos/extra-repos.done: $(LOCAL_MIRROR)/extra-repos/extra.repo
$(BUILD_DIR)/mirror/centos/extra-repos.done: $(BUILD_DIR)/mirror/centos/extra-repos-download.done
$(BUILD_DIR)/mirror/centos/extra-repos.done:
	$(foreach repo,$(EXTRA_RPM_REPOS),$(call extra_repo_metadata,$(repo));)
	$(ACTION.TOUCH)

define extra_repo_download
mkdir -p "$(extra_centos_empty_installroot)/cache" ;
set -ex ; env TMPDIR="$(extra_centos_empty_installroot)/cache" \
    TMP="$(extra_centos_empty_installroot)/cache" \
    reposync --downloadcomps --plugins --delete --arch=$(CENTOS_ARCH) \
    --cachedir="$(extra_centos_empty_installroot)/cache" \
    -c $(BUILD_DIR)/mirror/centos/etc/yum.conf --repoid=$(call get_repo_name,$1) \
    -p $(LOCAL_MIRROR)/extra-repos/
endef

define extra_repo_metadata
set -ex ; createrepo -g $(LOCAL_MIRROR)/extra-repos/$(call get_repo_name,$1)/comps.xml \
    -o $(LOCAL_MIRROR)/extra-repos/$(call get_repo_name,$1)/ $(LOCAL_MIRROR)/extra-repos/$(call get_repo_name,$1)/
endef
