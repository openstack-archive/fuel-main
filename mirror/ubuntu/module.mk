.PHONY: mirror-ubuntu repo-ubuntu

mirror-ubuntu: $(BUILD_DIR)/mirror/ubuntu/mirror.done
repo-ubuntu: $(BUILD_DIR)/mirror/ubuntu/repo.done

# Two operation modes:
# USE_MIRROR=none - mirroring mode, rsync full mirror from internal build server
# USE_MIRROR=<any_other_value> - ISO building mode, get repository for current product release only
$(BUILD_DIR)/mirror/ubuntu/build.done: 	$(BUILD_DIR)/mirror/ubuntu/mirror.done
ifneq ($(BUILD_PACKAGES),0)
    $(BUILD_DIR)/mirror/ubuntu/build.done:	$(BUILD_DIR)/mirror/ubuntu/repo.done
endif

$(BUILD_DIR)/mirror/ubuntu/aptly.conf:
	mkdir -p $(BUILD_DIR)/mirror/ubuntu/aptly.conf 
	echo '{"rootDir": "$(BUILD_DIR)/mirror/ubuntu/aptly/"}' > $(BUILD_DIR)/mirror/ubuntu/aptly.conf 
	$(ACTION.TOUCH)


$(BUILD_DIR)/mirror/ubuntu/repo.done: $(BUILD_DIR)/mirror/ubuntu/aptly.conf $(BUILD_DIR)/mirror/ubuntu/mirror.done
	mv $(LOCAL_MIRROR_UBUNTU) $(LOCAL_MIRROR_UBUNTU)_old
	rm -rf $(BUILD_DIR)/mirror/ubuntu/aptly/*
	aptly -config=$(BUILD_DIR)/mirror/ubuntu/aptly.conf repo create $(PRODUCT_NAME)$(PRODUCT_VERSION)-main
	aptly -config=$(BUILD_DIR)/mirror/ubuntu/aptly.conf repo create $(PRODUCT_NAME)$(PRODUCT_VERSION)-restricted
	aptly -config=$(BUILD_DIR)/mirror/ubuntu/aptly.conf repo add mos6.1-main $(LOCAL_MIRROR_UBUNTU)_old/
	aptly -config=$(BUILD_DIR)/mirror/ubuntu/aptly.conf repo add mos6.1-main $(BUILD_DIR)/packages/deb/packages/ 
	aptly -config=$(BUILD_DIR)/mirror/ubuntu/aptly.conf publish repo -architectures="amd64,i386,source" -distribution=\"$(PRODUCT_NAME)$(PRODUCT_VERSION)\" -component=main,restricted -skip-signing=true -origin=Mirantis -label=$(PRODUCT_NAME)$(PRODUCT_VERSION) -force-overwrite=true $(PRODUCT_NAME)$(PRODUCT_VERSION)-main $(PRODUCT_NAME)$(PRODUCT_VERSION)-restricted
	mkdir -p $(LOCAL_MIRROR_UBUNTU)
#	rm -rf $(LOCAL_MIRROR_UBUNTU)_old
	cp -r $(BUILD_DIR)/mirror/ubuntu/aptly/public/* $(LOCAL_MIRROR_UBUNTU)/
	$(ACTION.TOUCH)



$(BUILD_DIR)/mirror/ubuntu/mirror.done:
	mkdir -p $(LOCAL_MIRROR_UBUNTU)
ifeq (none,$(strip $(USE_MIRROR)))
	set -ex; rsync -aPtvz $(MIRROR_FUEL_UBUNTU)::$(PRODUCT_NAME)-ubuntu $(LOCAL_MIRROR_UBUNTU)/
else
	set -ex; debmirror --method=$(MIRROR_UBUNTU_METHOD) --progress --checksums --nocleanup --host=$(MIRROR_UBUNTU) --root=$(MIRROR_UBUNTU_ROOT) \
	--arch=$(UBUNTU_ARCH) --dist=$(PRODUCT_NAME)$(PRODUCT_VERSION) --nosource --exclude=".*-dbg_.*\.deb\$$" --ignore-release-gpg --rsync-extra=none \
	--section=$(MIRROR_UBUNTU_SECTION) $(LOCAL_MIRROR_UBUNTU)/
	rm -rf $(LOCAL_MIRROR_UBUNTU)/.temp $(LOCAL_MIRROR_UBUNTU)/project
endif
	$(ACTION.TOUCH)
