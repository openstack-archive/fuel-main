include $(SOURCE_DIR)/packages/rpm/module.mk
include $(SOURCE_DIR)/packages/eggs/module.mk
include $(SOURCE_DIR)/packages/gems/module.mk
include $(SOURCE_DIR)/packages/docker/module.mk

.PHONY: packages

$(BUILD_DIR)/packages/build.done: \
		$(BUILD_DIR)/packages/rpm/build.done \
		$(BUILD_DIR)/packages/eggs/build.done \
		$(BUILD_DIR)/packages/gems/build.done \
		$(BUILD_DIR)/packages/docker/build.done
	$(ACTION.TOUCH)

packages: $(BUILD_DIR)/packages/build.done
