.PHONY: mirror-ubuntu

mirror-ubuntu: $(BUILD_DIR)/mirror/ubuntu/build.done

# Two operation modes:
# USE_MIRROR=none - mirroring mode, rsync full mirror from internal build server
# USE_MIRROR=<any_other_value> - ISO building mode, get repository for current product release only
$(BUILD_DIR)/mirror/ubuntu/build.done:
	mkdir -p $(LOCAL_MIRROR_UBUNTU)
ifeq (none,$(strip $(USE_MIRROR)))
	set -ex; rsync -aPtvz $(MIRROR_FUEL_UBUNTU)::$(PRODUCT_NAME)-ubuntu $(LOCAL_MIRROR_UBUNTU)/
else
	set -ex; debmirror --method=$(MIRROR_UBUNTU_METHOD) --progress --checksums --nocleanup --host=$(MIRROR_UBUNTU) --root=$(MIRROR_UBUNTU_ROOT) \
	--arch=$(UBUNTU_ARCH) --dist=$(PRODUCT_NAME)$(PRODUCT_VERSION) --nosource --exclude=".*-dbg_.*\.deb\$$" --ignore-release-gpg --rsync-extra=none \
	$(LOCAL_MIRROR_UBUNTU)/
	rm -rf $(LOCAL_MIRROR_UBUNTU)/.temp $(LOCAL_MIRROR_UBUNTU)/project
endif
	$(ACTION.TOUCH)
