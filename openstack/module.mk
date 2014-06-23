include $(SOURCE_DIR)/openstack/rpm/module.mk

.PHONY: openstack

ifneq ($(BUILD_OPENSTACK_PACKAGES),0)
$(BUILD_DIR)/openstack/build.done: \
		$(BUILD_DIR)/openstack/rpm/build.done
endif

$(BUILD_DIR)/openstack/build.done:
	$(ACTION.TOUCH)

openstack: $(BUILD_DIR)/openstack/build.done
