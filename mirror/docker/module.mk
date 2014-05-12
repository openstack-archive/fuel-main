.PHONY: clean-docker
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/docker/base-images.mk

clean: clean-docker

clean-docker:
	pgrep docker && (sudo docker rm -f `sudo docker ps -aq`; sudo docker rmi `sudo docker images -q`) || exit 0

$(BUILD_DIR)/mirror/docker/build.done: \
		$(BUILD_DIR)/mirror/docker/base-images.done
	$(ACTION.TOUCH)
