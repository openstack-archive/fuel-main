include $(SOURCE_DIR)/packages/rpm/module.mk
include $(SOURCE_DIR)/packages/deb/module.mk

.PHONY: packages

ifneq ($(BUILD_PACKAGES),0)
$(BUILD_DIR)/packages/build.done: \
		$(BUILD_DIR)/packages/deb/build.done \
		$(BUILD_DIR)/packages/rpm/build.done
endif

$(BUILD_DIR)/packages/build.done: \
		$(BUILD_DIR)/packages/deb/build.done
	$(ACTION.TOUCH)

packages: $(BUILD_DIR)/packages/build.done
