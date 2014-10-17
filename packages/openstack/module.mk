include $(SOURCE_DIR)/packages/openstack/rpm/module.mk
include $(SOURCE_DIR)/packages/openstack/deb/module.mk

.PHONY: openstack

ifneq ($(strip $(BUILD_OPENSTACK_PACKAGES)),)
$(BUILD_DIR)/openstack/build.done: \
		$(BUILD_DIR)/openstack/rpm/build.done \
		$(BUILD_DIR)/openstack/deb/build.done
endif

$(BUILD_DIR)/openstack/build.done:
	$(ACTION.TOUCH)

openstack: $(BUILD_DIR)/openstack/build.done
