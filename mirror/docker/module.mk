# This module downloads Fuel master node docker images.
include $(SOURCE_DIR)/mirror/docker/images.mk

$(BUILD_DIR)/mirror/docker/build.done: \
		$(BUILD_DIR)/mirror/docker/images.done
	$(ACTION.TOUCH)
