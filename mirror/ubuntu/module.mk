.PHONY: mirror-ubuntu
# This module downloads ubuntu installation images.
#include $(SOURCE_DIR)/mirror/ubuntu/boot.mk

include $(SOURCE_DIR)/mirror/ubuntu/mirror.mk

mirror-ubuntu: $(BUILD_DIR)/mirror/ubuntu/build.done

$(BUILD_DIR)/mirror/ubuntu/build.done: \
		$(BUILD_DIR)/mirror/ubuntu/mirror.done
	$(ACTION.TOUCH)
