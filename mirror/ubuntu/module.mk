.PHONY: clean-ubuntu chroot-ubuntu
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/ubuntu/boot.mk
include $(SOURCE_DIR)/mirror/ubuntu/createchroot.mk

clean: clean-ubuntu

clean-ubuntu:
	(mount -l | grep -q $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/proc && sudo umount $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/proc) || exit 0
	sudo rm -rf $(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/chroot/

$(BUILD_DIR)/mirror/ubuntu/build.done: \
		$(BUILD_DIR)/mirror/ubuntu/boot.done \
		$(BUILD_DIR)/mirror/ubuntu/createchroot.done \
		$(BUILD_DIR)/mirror/ubuntu/mkrepo.done
	$(ACTION.TOUCH)

chroot-ubuntu: \
		$(BUILD_DIR)/mirror/ubuntu/createchroot.done
