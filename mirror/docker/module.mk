.PHONY: clean-docker
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/docker/base-images.mk

clean: clean-docker

clean-docker:
	timeout -k5 4 docker ps && docker rm -f `docker ps -a | awk '/fuel/ {print $$1}'` || true
	timeout -k5 4 docker images && docker rmi -f `docker images | awk '/fuel/ { print $$3; }'` || true

$(BUILD_DIR)/mirror/docker/build.done: \
		$(BUILD_DIR)/mirror/docker/base-images.done
	$(ACTION.TOUCH)
