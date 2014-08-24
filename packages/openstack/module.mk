include $(SOURCE_DIR)/packages/openstack/rpm/module_mock.mk

.PHONY: openstack

ifneq ($(BUILD_OPENSTACK_PACKAGES),0)
$(BUILD_DIR)/openstack/build.done: \
		$(BUILD_DIR)/openstack/rpm/build.done
endif

$(BUILD_DIR)/openstack/build.done:
	$(ACTION.TOUCH)

openstack: $(BUILD_DIR)/openstack/build.done
