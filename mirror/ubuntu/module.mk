.PHONY: clean-ubuntu mirror-ubuntu
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/ubuntu/boot.mk
include $(SOURCE_DIR)/mirror/ubuntu/createchroot.mk
include $(SOURCE_DIR)/mirror/ubuntu/download.mk

clean: clean-ubuntu
mirror-ubuntu: $(BUILD_DIR)/mirror/ubuntu/build.done

clean-ubuntu:
	(mount -l | grep -q $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/proc && sudo umount $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/proc) || exit 0

ifeq ($(USE_MIRROR),none)
$(BUILD_DIR)/mirror/ubuntu/build.done: \
		$(BUILD_DIR)/mirror/ubuntu/boot.done \
		$(BUILD_DIR)/mirror/ubuntu/createchroot.done
	$(ACTION.TOUCH)
else
$(BUILD_DIR)/mirror/ubuntu/build.done: \
		$(BUILD_DIR)/mirror/ubuntu/download.done
	$(ACTION.TOUCH)
endif