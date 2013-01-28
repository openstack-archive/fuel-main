# This module downloads required rpm packages and creates rpm repository.
include $(SOURCE_DIR)/mirror/centos/repo.mk
# This module downloads centos installation images.
include $(SOURCE_DIR)/mirror/centos/boot.mk

$(BUILD_DIR)/mirror/centos/build.done: \
		$(BUILD_DIR)/mirror/centos/repo.done \
		$(BUILD_DIR)/mirror/centos/boot.done
	$(ACTION.TOUCH)
