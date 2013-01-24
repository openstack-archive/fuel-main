include $(SOURCE_DIR)/mirror/src/module.mk
include $(SOURCE_DIR)/mirror/centos/module.mk
include $(SOURCE_DIR)/mirror/eggs/module.mk
include $(SOURCE_DIR)/mirror/gems/module.mk

.PHONY: mirror

$(BUILD_DIR)/mirror/build.done: \
		$(BUILD_DIR)/mirror/src/build.done \
		$(BUILD_DIR)/mirror/centos/build.done \
		$(BUILD_DIR)/mirror/eggs/build.done \
		$(BUILD_DIR)/mirror/gems/build.done
	$(ACTION.TOUCH)

mirror: $(BUILD_DIR)/mirror/build.done
