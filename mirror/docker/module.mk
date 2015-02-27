.PHONY: clean-docker
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/docker/base-images.mk

clean: clean-docker

clean-docker:
	-sudo sh -c "docker ps -aq | xargs --no-run-if-empty docker rm -f"
	-sudo sh -c "docker images | awk '/fuel|none/ { print \$$3; }' | xargs --no-run-if-empty docker rmi -f"

$(BUILD_DIR)/mirror/docker/build.done: \
		$(BUILD_DIR)/mirror/docker/base-images.done
	$(ACTION.TOUCH)
