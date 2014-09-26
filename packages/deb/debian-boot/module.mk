.PHONY: clean-ubuntu-packages
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/ubuntu/initrd.mk
include $(SOURCE_DIR)/mirror/ubuntu/createchroot.mk

clean-ubuntu-packages:
	sudo rm -rf $(BUILD_DIR)/packages/ubuntu/

$(BUILD_DIR)/packages/ubuntu/build.done: \
		$(BUILD_DIR)/mirror/ubuntu/initrd.done \
	$(ACTION.TOUCH)
