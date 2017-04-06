.PHONY: clean-docker

clean: clean-docker

clean-docker:
	-sudo sh -c "docker ps -aq | xargs --no-run-if-empty docker rm -f"
	-sudo sh -c "docker images | awk '/fuel|none/ { print \$$3; }' | xargs --no-run-if-empty docker rmi -f"

$(BUILD_DIR)/mirror/docker/build.done:
	@mkdir -p $(BUILD_DIR)/mirror/docker
	$(ACTION.TOUCH)
