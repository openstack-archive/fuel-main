.PHONY: mirror-deb

mirror-deb: $(BUILD_DIR)/mirror/deb/mirror.done

$(BUILD_DIR)/mirror/deb/mirror.done:
ifeq (none,$(strip $(USE_MIRROR)))
	mkdir -p $(LOCAL_MIRROR_UBUNTU)
	set -ex; rsync -aPtvz $(MIRROR_FUEL_UBUNTU) $(LOCAL_MIRROR_UBUNTU)/
endif
	$(ACTION.TOUCH)

