.PHONY: clean-docker
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/docker/base-images.mk

clean: clean-docker

clean-docker:
	sudo umount -l `grep "$(BUILD_DIR)/docker" /proc/mounts | awk '{print $$2}' | sort -r` /dev/notfound || :


$(BUILD_DIR)/mirror/docker/build.done: \
		$(BUILD_DIR)/mirror/docker/base-images.done
	$(ACTION.TOUCH)
