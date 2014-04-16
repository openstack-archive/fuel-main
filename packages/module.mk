include $(SOURCE_DIR)/packages/rpm/module.mk

.PHONY: packages

ifneq ($(NO_PACKAGES_BUILD),0)
$(BUILD_DIR)/packages/build.done: \
		$(BUILD_DIR)/packages/rpm/build.done
endif

$(BUILD_DIR)/packages/build.done:
	$(ACTION.TOUCH)

packages: $(BUILD_DIR)/packages/build.done
