ifeq ($(CACHE_RHEL),1)
# This module downloads required rpm packages and creates rpm repository.
include $(SOURCE_DIR)/mirror/rhel/repo.mk
# This module downloads installation images.
include $(SOURCE_DIR)/mirror/rhel/boot.mk

$(BUILD_DIR)/mirror/rhel/build.done: \
		$(BUILD_DIR)/mirror/rhel/repo.done \
		$(BUILD_DIR)/mirror/rhel/boot.done
	$(ACTION.TOUCH)
else
$(BUILD_DIR)/mirror/rhel/build.done:
	$(ACTION.TOUCH)
endif
