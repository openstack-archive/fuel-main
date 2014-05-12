.PHONY: clean-docker
# This module downloads ubuntu installation images.
include $(SOURCE_DIR)/mirror/docker/base-images.mk

clean: clean-docker

clean-docker:
	timeout -k5 4 sudo docker ps && sudo docker rm -f `sudo docker ps -a | awk '/fuel/ {print $$1}'` || true
	timeout -k5 4 sudo docker images && sudo docker rmi -f `sudo docker images | awk '/fuel/ { print $$3; }'`) || true

$(BUILD_DIR)/mirror/docker/build.done: \
		$(BUILD_DIR)/mirror/docker/base-images.done
	$(ACTION.TOUCH)
