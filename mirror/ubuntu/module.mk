# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/ubuntu/boot.mk
include $(SOURCE_DIR)/mirror/ubuntu/createchroot.mk

$(BUILD_DIR)/mirror/ubuntu/build.done: \
		$(BUILD_DIR)/mirror/ubuntu/boot.done \
		$(BUILD_DIR)/mirror/ubuntu/createchroot.done
	$(ACTION.TOUCH)
