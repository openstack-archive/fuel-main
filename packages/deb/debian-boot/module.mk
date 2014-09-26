.PHONY: clean-ubuntu-packages
include $(SOURCE_DIR)/packages/deb/debian-boot/initrd.mk

clean-ubuntu-packages:
	sudo rm -rf $(BUILD_DIR)/packages/deb/

$(BUILD_DIR)/packages/deb/debian-boot/build.done: \
		$(BUILD_DIR)/packages/deb/debian-boot/initrd.done
	$(ACTION.TOUCH)
