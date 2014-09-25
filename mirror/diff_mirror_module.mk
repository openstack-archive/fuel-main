.PHONY: diff-mirror centos-diff-repo ubuntu-diff-repo

diff-mirror: centos-diff-repo ubuntu-diff-repo

#############################
# CENTOS DIFF MIRROR ARTIFACT
#############################

define build_diff_centos_repo
# 1 - new version
# 2 - old version

# if old version is empty line, then we don't need to build diff repo
ifneq ($2,)
DIFF_CENTOS_REPO_ART_NAME:=$(DIFF_CENTOS_REPO_ART_BASE)-$1-$2.tar
centos-diff-repo: $(ARTS_DIR)/$$(DIFF_CENTOS_REPO_ART_NAME)
.DELETE_ON_ERROR: $(BUILD_DIR)/mirror/$$(DIFF_CENTOS_REPO_ART_NAME)

$(ARTS_DIR)/$$(DIFF_CENTOS_REPO_ART_NAME): $(BUILD_DIR)/mirror/$$(DIFF_CENTOS_REPO_ART_NAME)
	@mkdir -p $$(@D)
	cp $$< $$@

$(BUILD_DIR)/mirror/$$(DIFF_CENTOS_REPO_ART_NAME): NEWDIR=$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages
$(BUILD_DIR)/mirror/$$(DIFF_CENTOS_REPO_ART_NAME): OLDDIR=$(BUILD_DIR)/mirror/$2/centos-repo/Packages
$(BUILD_DIR)/mirror/$$(DIFF_CENTOS_REPO_ART_NAME): DIFFDIR=$(DIFF_MIRROR_CENTOS_BASE)-$1-$2/os/$(CENTOS_ARCH)/Packages
$(BUILD_DIR)/mirror/$$(DIFF_CENTOS_REPO_ART_NAME): \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/openstack/build.done
#	unpacking old version centos mirror
	mkdir -p $(BUILD_DIR)/mirror/$2
	tar xf $(DEPS_DIR)/$2/$(CENTOS_REPO_ART_NAME) -C $(BUILD_DIR)/mirror/$2
#	copying packages which differ from those in old version
	mkdir -p $$(DIFFDIR)
	/bin/bash $(SOURCE_DIR)/mirror/create_diff_mirrors.sh $$(NEWDIR) $$(OLDDIR) $$(DIFFDIR)
#	creating diff mirror
	createrepo -o $$(DIFFDIR)/../ $$(DIFFDIR)/../
	rpm -qi -p $$(DIFFDIR)/*.rpm | $(SOURCE_DIR)/iso/pkg-versions.awk > $(DIFF_MIRROR_CENTOS_BASE)-$1-$2/centos-versions.yaml
	tar cf $$@ -C $(DIFF_MIRROR_CENTOS_BASE)-$1-$2 --xform s:^:centos_updates-$1-$2/: .
endif # ifneq ($2,)
endef # build_diff_centos_repo

$(foreach diff,$(UPGRADE_VERSIONS),$(eval $(call build_diff_centos_repo,$(shell echo $(diff) | awk -F':' '{print $$1}'),$(shell echo $(diff) | awk -F':' '{print $$2}'))))

#############################
# UBUNTU DIFF MIRROR ARTIFACT
#############################

define build_diff_ubuntu_repo
# 1 - new version
# 2 - old version

# if old version is empty line, then we don't need to build diff repo
ifneq ($2,)
DIFF_UBUNTU_REPO_ART_NAME:=$(DIFF_UBUNTU_REPO_ART_BASE)-$1-$2.tar
ubuntu-diff-repo: $(ARTS_DIR)/$$(DIFF_UBUNTU_REPO_ART_NAME)
.DELETE_ON_ERROR: $(BUILD_DIR)/mirror/$$(DIFF_UBUNTU_REPO_ART_NAME)

$(ARTS_DIR)/$$(DIFF_UBUNTU_REPO_ART_NAME): $(BUILD_DIR)/mirror/$$(DIFF_UBUNTU_REPO_ART_NAME)
	@mkdir -p $$(@D)
	cp $$< $$@

$(BUILD_DIR)/mirror/$$(DIFF_UBUNTU_REPO_ART_NAME): NEWDIR=$(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main
$(BUILD_DIR)/mirror/$$(DIFF_UBUNTU_REPO_ART_NAME): OLDDIR=$(BUILD_DIR)/mirror/$2/ubuntu-repo/pool/main
$(BUILD_DIR)/mirror/$$(DIFF_UBUNTU_REPO_ART_NAME): DIFFDIR=$(DIFF_MIRROR_UBUNTU_BASE)-$1-$2/pool/main
$(BUILD_DIR)/mirror/$$(DIFF_UBUNTU_REPO_ART_NAME): \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/openstack/build.done
#	unpacking old version ubuntu mirror
	mkdir -p $(BUILD_DIR)/mirror/$2
	tar xf $(DEPS_DIR)/$2/$(UBUNTU_REPO_ART_NAME) -C $(BUILD_DIR)/mirror/$2
#	copying packages which differ from those in old version
	mkdir -p $$(DIFFDIR)
	/bin/bash $(SOURCE_DIR)/mirror/create_diff_mirrors.sh $$(NEWDIR) $$(OLDDIR) $$(DIFFDIR)
#	creating diff mirror
	dpkg-scanpackages -m $$(DIFFDIR) > $$(DIFFDIR)/../Packages
	gzip -9c $$(DIFFDIR)/../Packages > $$(DIFFDIR)/../Packages.gz
	cat $$(DIFFDIR)/../Packages | $(SOURCE_DIR)/iso/pkg-versions.awk > $(DIFF_MIRROR_UBUNTU_BASE)-$1-$2/ubuntu-versions.yaml
	tar cf $$@ -C $(DIFF_MIRROR_UBUNTU_BASE)-$1-$2 --xform s:^:ubuntu_updates-$1-$2/: .
endif # ifneq ($2,)
endef # build_diff_ubuntu_repo

$(foreach diff,$(UPGRADE_VERSIONS),$(eval $(call build_diff_ubuntu_repo,$(shell echo $(diff) | awk -F':' '{print $$1}'),$(shell echo $(diff) | awk -F':' '{print $$2}'))))
