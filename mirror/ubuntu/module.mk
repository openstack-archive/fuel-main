.PHONY: mirror-ubuntu
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/ubuntu/boot.mk

mirror-ubuntu: $(BUILD_DIR)/mirror/ubuntu/build.done

$(BUILD_DIR)/mirror/ubuntu/repo.done: $(BUILD_DIR)/ubuntu_installer_kernel_version.mk
	$(MAKE) -f $(SOURCE_DIR)/mirror/ubuntu/repo.mk \
		MIRROR_UBUNTU=$(MIRROR_UBUNTU) \
		MIRROR_FUEL_UBUNTU=$(MIRROR_FUEL_UBUNTU) \
		MIRROR_UBUNTU_SECURITY=$(MIRROR_UBUNTU_SECURITY) \
		USE_MIRROR=$(USE_MIRROR) \
		EXTRA_DEB_REPOS='$(EXTRA_DEB_REPOS)' \
		UBUNTU_RELEASE=$(UBUNTU_RELEASE) \
		UBUNTU_RELEASE_NUMBER=$(UBUNTU_RELEASE_NUMBER) \
		UBUNTU_ARCH=$(UBUNTU_ARCH) \
		UBUNTU_KERNEL_FLAVOR=$(UBUNTU_KERNEL_FLAVOR) \
		LOCAL_MIRROR_UBUNTU=$(LOCAL_MIRROR_UBUNTU) \
		SOURCE_DIR=$(SOURCE_DIR) \
		BUILD_DIR=$(BUILD_DIR)
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/ubuntu/build.done: \
		$(BUILD_DIR)/mirror/ubuntu/boot.done \
		$(BUILD_DIR)/mirror/ubuntu/repo.done
	$(ACTION.TOUCH)
