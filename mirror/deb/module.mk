.PHONY: mirror-deb

mirror-deb: $(BUILD_DIR)/mirror/deb/build.done

# Two operation modes:
# USE_MIRROR=none - mirroring mode, rsync full mirror from internal build server
# USE_MIRROR=<any_other_value> - ISO building mode, get repository for current product release only

$(BUILD_DIR)/mirror/deb/build.done:
	mkdir -p $(LOCAL_MIRROR_UBUNTU)
ifeq (none,$(strip $(USE_MIRROR)))
	set -ex; rsync -aPtvz $(MIRROR_FUEL_UBUNTU) $(LOCAL_MIRROR_UBUNTU)/
else
	set -ex; debmirror --i18n --method=rsync --progress --host=$(MIRROR_UBUNTU) --arch=$(UBUNTU_ARCH) \
	--dist=$(UBUNTU_RELEASE) -r mos --nosource --exclude=".*-dbg_.*\.deb\$$" --ignore-release-gpg $(LOCAL_MIRROR_UBUNTU)/
	rm -rf $(LOCAL_MIRROR_UBUNTU)/.temp $(LOCAL_MIRROR_UBUNTU)/project
endif
	$(ACTION.TOUCH)

