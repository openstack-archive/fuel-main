# Two operation modes:
# USE_MIRROR=none - mirroring mode, rsync full mirror from internal build server
# USE_MIRROR=<any_other_value> - ISO building mode, get repository for current product release only

$(BUILD_DIR)/mirror/ubuntu/mirror.done:
	mkdir -p $(LOCAL_MIRROR_UBUNTU)
ifeq (none,$(strip $(USE_MIRROR)))
	set -ex; rsync -aPtvz $(MIRROR_FUEL_UBUNTU)::$(PRODUCT_NAME) $(LOCAL_MIRROR_UBUNTU)/
else
	set -ex; debmirror --method=http --progress --checksums --nocleanup --host=$(MIRROR_UBUNTU) --root=/mos/ubuntu/ --arch=$(UBUNTU_ARCH) \
	--dist=$(PRODUCT_NAME)$(PRODUCT_VERSION) --nosource --exclude=".*-dbg_.*\.deb\$$" --ignore-release-gpg --rsync-extra=none $(LOCAL_MIRROR_UBUNTU)/
	rm -rf $(LOCAL_MIRROR_UBUNTU)/.temp $(LOCAL_MIRROR_UBUNTU)/project
endif
	$(ACTION.TOUCH)
