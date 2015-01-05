.PHONY: clean-docker
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/docker/base-images.mk

clean: clean-docker

clean-docker:
	sudo sh -c 'docker ps && docker rm -f `docker ps -a | awk "/fuel/ {print $$1}"` 2>/dev/null || true'
	sudo sh -c 'docker images && docker rmi -f `docker images | awk "/fuel/ { print $$3; }"` 2>/dev/null || true'

$(BUILD_DIR)/mirror/docker/build.done: \
		$(BUILD_DIR)/mirror/docker/base-images.done
	$(ACTION.TOUCH)
