ifeq ($(USE_MOCK),Y)
include $(SOURCE_DIR)/packages/rpm/module_mock.mk
else
include $(SOURCE_DIR)/packages/rpm/module.mk
endif
include $(SOURCE_DIR)/packages/deb/module.mk

.PHONY: packages

ifneq ($(BUILD_PACKAGES),0)
$(BUILD_DIR)/packages/build.done: \
		$(BUILD_DIR)/packages/rpm/build.done $(BUILD_DIR)/packages/deb/build.done
endif

$(BUILD_DIR)/packages/build.done:
	$(ACTION.TOUCH)

packages: $(BUILD_DIR)/packages/build.done
