.PHONY: mirror_diff diff-repo

mirror_diff: $(BUILD_DIR)/mirror/mirror_diff.done

$(BUILD_DIR)/mirror/mirror_diff.done: \
	$(BUILD_DIR)/mirror/build.done

	mkdir -p $(DIFF_MIRROR_CENTOS_OS_PKGS)
	mkdir -p $(DIFF_MIRROR_UBUNTU_OS_PKGS)

	# centos
	/bin/bash $(SOURCE_DIR)/mirror/create_diff_mirrors.sh \
		$(LOCAL_MIRROR_CENTOS_OS_BASEURL)/Packages/ \
		/tmp/mirrors/5.1.1/centos/os/x86_64/Packages \
		$(DIFF_MIRROR_CENTOS_OS_PKGS)
	# ubuntu
	/bin/bash $(SOURCE_DIR)/mirror/create_diff_mirrors.sh \
		$(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/pool/main/ \
		/tmp/mirrors/5.1.1/ubuntu/pool/main \
		$(DIFF_MIRROR_UBUNTU_OS_PKGS)

	# create centos repo
	createrepo $(DIFF_MIRROR_CENTOS_OS_PKGS) -o $(DIFF_MIRROR_CENTOS_OS_PKGS)/../
	# create ubuntu repo
	dpkg-scanpackages -m $(DIFF_MIRROR_UBUNTU_OS_PKGS) > $(DIFF_MIRROR_UBUNTU_OS_PKGS)/../Packages
	gzip -9c $(DIFF_MIRROR_UBUNTU_OS_PKGS)/../Packages > $(DIFF_MIRROR_UBUNTU_OS_PKGS)/../Packages.gz

	$(ACTION.TOUCH)

########################
# DIFF_MIRROR ARTIFACT
########################
diff-repo: $(ARTS_DIR)/$(DIFF_CENTOS_ART_NAME) \
		$(ARTS_DIR)/$(DIFF_UBUNTU_ART_NAME)

$(ARTS_DIR)/$(DIFF_CENTOS_ART_NAME): $(BUILD_DIR)/mirror/$(DIFF_CENTOS_ART_NAME)
	$(ACTION.COPY)

DIFF_CENTOS_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(DIFF_CENTOS_ART_NAME))

ifdef DIFF_CENTOS_DEP_FILE
$(BUILD_DIR)/mirror/$(DIFF_CENTOS_ART_NAME):
	$(ACTION.COPY)
else
$(BUILD_DIR)/mirror/$(DIFF_CENTOS_ART_NAME): \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/openstack/build.done \
		$(BUILD_DIR)/mirror/mirror_diff.done

		rpm -qi -p $(DIFF_MIRROR_CENTOS_OS_PKGS)/*.rpm | $(SOURCE_DIR)/iso/pkg-versions.awk > $(DIFF_MIRROR_CENTOS)/centos-versions.yaml

		tar cf $@ -C $(LOCAL_MIRROR) --xform s:^:centos-diff-repo/: $(DIFF_MIRROR_CENTOS)
endif


$(ARTS_DIR)/$(DIFF_UBUNTU_ART_NAME): $(BUILD_DIR)/mirror/$(DIFF_UBUNTU_ART_NAME)
	$(ACTION.COPY)

DIFF_UBUNTU_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(DIFF_UBUNTU_ART_NAME))

ifdef DIFF_UBUNTU_DEP_FILE
$(BUILD_DIR)/mirror/$(DIFF_UBUNTU_ART_NAME):
	$(ACTION.COPY)
else
$(BUILD_DIR)/mirror/$(DIFF_UBUNTU_ART_NAME): \
		$(BUILD_DIR)/mirror/build.done \
		$(BUILD_DIR)/packages/build.done \
		$(BUILD_DIR)/mirror/mirror_diff.done

		cat $(DIFF_MIRROR_UBUNTU_OS_PKGS)/../Packages | $(SOURCE_DIR)/iso/pkg-versions.awk > $(DIFF_MIRROR_UBUNTU)/ubuntu-versions.yaml

		tar cf $@ -C $(LOCAL_MIRROR) --xform s:^:ubuntu-diff-repo/: $(DIFF_MIRROR_UBUNTU)
endif
