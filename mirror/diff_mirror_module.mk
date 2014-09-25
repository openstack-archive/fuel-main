#############################
# CENTOS DIFF MIRROR ARTIFACT
#############################
ifneq ($(BASE_VERSION),)
.PHONY: centos-diff-repo

DIFF_CENTOS_REPO_ART_NAME:=$(DIFF_CENTOS_REPO_ART_BASE)-$(CURRENT_VERSION)-$(BASE_VERSION).tar
centos-diff-repo: $(ARTS_DIR)/$(DIFF_CENTOS_REPO_ART_NAME)

$(ARTS_DIR)/$(DIFF_CENTOS_REPO_ART_NAME): $(BUILD_DIR)/mirror/$(DIFF_CENTOS_REPO_ART_NAME)
	$(ACTION.COPY)

DIFF_CENTOS_REPO_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(DIFF_CENTOS_REPO_ART_NAME))

ifneq ($(DIFF_CENTOS_REPO_DEP_FILE),)
$(BUILD_DIR)/mirror/$(DIFF_CENTOS_REPO_ART_NAME): $(DIFF_CENTOS_REPO_DEP_FILE)
	$(ACTION.COPY)
else
.DELETE_ON_ERROR: $(BUILD_DIR)/mirror/$(DIFF_CENTOS_REPO_ART_NAME)
CURRENT_CENTOS_REPO_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(CENTOS_REPO_ART_NAME))
ifneq ($(CENTOS_REPO_DEP_FILE),)
$(BUILD_DIR)/mirror/$(DIFF_CENTOS_REPO_ART_NAME): NEWDIR=$(BUILD_DIR)/mirror/$(CURRENT_VERSION)/centos-repo/Packages
$(BUILD_DIR)/mirror/$(DIFF_CENTOS_REPO_ART_NAME): $(BUILD_DIR)/mirror/centos_repo_current.done
$(BUILD_DIR)/mirror/centos_repo_current.done: $(CURRENT_CENTOS_REPO_DEP_FILE)
	mkdir -p $(BUILD_DIR)/mirror/$(CURRENT_VERSION)
	tar xf $(CURRENT_CENTOS_REPO_DEP_FILE) -C $(BUILD_DIR)/mirror/$(CURRENT_VERSION)
	$(ACTION.TOUCH)
else
$(BUILD_DIR)/mirror/$(DIFF_CENTOS_REPO_ART_NAME): NEWDIR=$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages
$(BUILD_DIR)/mirror/$(DIFF_CENTOS_REPO_ART_NAME): $(BUILD_DIR)/mirror/centos_repo_current.done
$(BUILD_DIR)/mirror/centos_repo_current.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/openstack/build.done
	$(ACTION.TOUCH)

endif
$(BUILD_DIR)/mirror/$(DIFF_CENTOS_REPO_ART_NAME): BASEDIR=$(BUILD_DIR)/mirror/$(BASE_VERSION)/centos-repo/Packages
$(BUILD_DIR)/mirror/$(DIFF_CENTOS_REPO_ART_NAME): DIFFDIR=$(DIFF_MIRROR_CENTOS_BASE)-$(CURRENT_VERSION)-$(BASE_VERSION)/os/$(CENTOS_ARCH)/Packages
$(BUILD_DIR)/mirror/$(DIFF_CENTOS_REPO_ART_NAME): | $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml
#	unpacking old version centos mirror
	mkdir -p $(BUILD_DIR)/mirror/$(BASE_VERSION)
	tar xf $(DEPS_DIR)/$(BASE_VERSION)/$(CENTOS_REPO_ART_NAME) -C $(BUILD_DIR)/mirror/$(BASE_VERSION)
#	copying packages which differ from those in base version
	mkdir -p $(DIFFDIR)
	/bin/bash $(SOURCE_DIR)/mirror/create_diff_mirrors.sh $(NEWDIR) $(BASEDIR) $(DIFFDIR)
#	creating diff mirror
	cp $(LOCAL_MIRROR_CENTOS_OS_BASEURL)/comps.xml $(DIFFDIR)/../comps.xml
	createrepo -g $(DIFFDIR)/../comps.xml -o $(DIFFDIR)/../ $(DIFFDIR)/../
	rpm -qi -p $(DIFFDIR)/*.rpm | $(SOURCE_DIR)/iso/pkg-versions.awk > $(DIFF_MIRROR_CENTOS_BASE)-$(CURRENT_VERSION)-$(BASE_VERSION)/centos-versions.yaml
	tar cf $@ -C $(DIFF_MIRROR_CENTOS_BASE)-$(CURRENT_VERSION)-$(BASE_VERSION) --xform s:^:centos_updates-$(CURRENT_VERSION)-$(BASE_VERSION)/: .
endif # ifneq ($(BASE_VERSION),)


#############################
# UBUNTU DIFF MIRROR ARTIFACT
#############################
ifneq ($(BASE_VERSION),)
.PHONY: ubuntu-diff-repo

DIFF_UBUNTU_REPO_ART_NAME:=$(DIFF_UBUNTU_REPO_ART_BASE)-$(CURRENT_VERSION)-$(BASE_VERSION).tar
ubuntu-diff-repo: $(ARTS_DIR)/$(DIFF_UBUNTU_REPO_ART_NAME)

$(ARTS_DIR)/$(DIFF_UBUNTU_REPO_ART_NAME): $(BUILD_DIR)/mirror/$(DIFF_UBUNTU_REPO_ART_NAME)
	$(ACTION.COPY)

DIFF_UBUNTU_REPO_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(DIFF_UBUNTU_REPO_ART_NAME))

ifneq ($(DIFF_UBUNTU_REPO_DEP_FILE),)
$(BUILD_DIR)/mirror/$(DIFF_UBUNTU_REPO_ART_NAME): $(DIFF_UBUNTU_REPO_DEP_FILE)
	$(ACTION.COPY)
else
.DELETE_ON_ERROR: $(BUILD_DIR)/mirror/$(DIFF_UBUNTU_REPO_ART_NAME)
CURRENT_UBUNTU_REPO_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(UBUNTU_REPO_ART_NAME))
ifneq ($(UBUNTU_REPO_DEP_FILE),)
$(BUILD_DIR)/mirror/$(DIFF_UBUNTU_REPO_ART_NAME): NEWDIR=$(BUILD_DIR)/mirror/$(CURRENT_VERSION)/ubuntu-repo/pool/main
$(BUILD_DIR)/mirror/$(DIFF_UBUNTU_REPO_ART_NAME): $(BUILD_DIR)/mirror/ubuntu_repo_current.done
$(BUILD_DIR)/mirror/ubuntu_repo_current.done: $(CURRENT_UBUNTU_REPO_DEP_FILE)
	mkdir -p $(BUILD_DIR)/mirror/$(CURRENT_VERSION)
	tar xf $(CURRENT_UBUNTU_REPO_DEP_FILE) -C $(BUILD_DIR)/mirror/$(CURRENT_VERSION)
	$(ACTION.TOUCH)
else
$(BUILD_DIR)/mirror/$(DIFF_UBUNTU_REPO_ART_NAME): NEWDIR=$(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main
$(BUILD_DIR)/mirror/$(DIFF_UBUNTU_REPO_ART_NAME): $(BUILD_DIR)/mirror/ubuntu_repo_current.done
$(BUILD_DIR)/mirror/ubuntu_repo_current.done: \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/openstack/build.done
	$(ACTION.TOUCH)

endif
$(BUILD_DIR)/mirror/$(DIFF_UBUNTU_REPO_ART_NAME): BASEDIR=$(BUILD_DIR)/mirror/$(BASE_VERSION)/ubuntu-repo/pool/main
$(BUILD_DIR)/mirror/$(DIFF_UBUNTU_REPO_ART_NAME): DIFFDIR=$(DIFF_MIRROR_UBUNTU_BASE)-$(CURRENT_VERSION)-$(BASE_VERSION)/pool/main
$(BUILD_DIR)/mirror/$(DIFF_UBUNTU_REPO_ART_NAME):
#	unpacking old version ubuntu mirror
	mkdir -p $(BUILD_DIR)/mirror/$(BASE_VERSION)
	tar xf $(DEPS_DIR)/$(BASE_VERSION)/$(UBUNTU_REPO_ART_NAME) -C $(BUILD_DIR)/mirror/$(BASE_VERSION)
#	copying packages which differ from those in old version
	mkdir -p $(DIFFDIR)
	/bin/bash $(SOURCE_DIR)/mirror/create_diff_mirrors.sh $(NEWDIR) $(BASEDIR) $(DIFFDIR)
#	creating diff mirror
	dpkg-scanpackages -m $(DIFFDIR) > $(DIFFDIR)/../Packages
	gzip -9c $(DIFFDIR)/../Packages > $(DIFFDIR)/../Packages.gz
	cat $(DIFFDIR)/../Packages | $(SOURCE_DIR)/iso/pkg-versions.awk > $(DIFF_MIRROR_UBUNTU_BASE)-$(CURRENT_VERSION)-$(BASE_VERSION)/ubuntu-versions.yaml
	tar cf $@ -C $(DIFF_MIRROR_UBUNTU_BASE)-$(CURRENT_VERSION)-$(BASE_VERSION) --xform s:^:ubuntu_updates-$(CURRENT_VERSION)-$(BASE_VERSION)/: .
endif # ifneq ($(BASE_VERSION),)
