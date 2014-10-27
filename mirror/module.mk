.PHONY: mirror clean clean-mirror

mirror: $(BUILD_DIR)/mirror/build.done

clean: clean-mirror

clean-mirror: clean-ubuntu
	sudo rm -rf $(BUILD_DIR)/mirror

include $(SOURCE_DIR)/mirror/centos/module.mk
include $(SOURCE_DIR)/mirror/ubuntu/module.mk
include $(SOURCE_DIR)/mirror/docker/module.mk
include $(SOURCE_DIR)/mirror/diff_mirror_module.mk

$(BUILD_DIR)/mirror/build.done: \
		$(BUILD_DIR)/mirror/centos/build.done \
		$(BUILD_DIR)/mirror/ubuntu/build.done \
		$(BUILD_DIR)/mirror/docker/build.done
	$(ACTION.TOUCH)
