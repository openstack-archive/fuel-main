include $(SOURCE_DIR)/packages/deb/debian-boot/module.mk

$(BUILD_DIR)/packages/deb/build.done: $(BUILD_DIR)/packages/deb/debian-boot/build.done
	$(ACTION.TOUCH)

