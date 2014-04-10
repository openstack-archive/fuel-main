.PHONY: mirror clean clean-mirror

mirror: $(BUILD_DIR)/mirror/build.done

clean: clean-mirror

clean-mirror: clean-mirror-eggs clean-ubuntu
	sudo rm -rf $(BUILD_DIR)/mirror

include $(SOURCE_DIR)/mirror/src/module.mk
include $(SOURCE_DIR)/mirror/centos/module.mk
include $(SOURCE_DIR)/mirror/ubuntu/module.mk
include $(SOURCE_DIR)/mirror/rhel/module.mk
include $(SOURCE_DIR)/mirror/eggs/module.mk
include $(SOURCE_DIR)/mirror/gems/module.mk

$(BUILD_DIR)/mirror/build.done: \
		$(BUILD_DIR)/mirror/src/build.done \
		$(BUILD_DIR)/mirror/centos/build.done \
		$(BUILD_DIR)/mirror/ubuntu/build.done \
		$(BUILD_DIR)/mirror/rhel/build.done \
		$(BUILD_DIR)/mirror/eggs/build.done \
		$(BUILD_DIR)/mirror/gems/build.done
	$(ACTION.TOUCH)

