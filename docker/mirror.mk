BASE_IMAGE_FILES:=centos.tar.xz busybox.tar.xz

MIRROR_DOCKER_BASEURL?=$(MIRROR_DOCKER)
LOCAL_MIRROR_DOCKER_BASEURL?=$(BUILD_DIR)/local_mirror_docker

$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_IMAGE_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(MIRROR_DOCKER_BASEURL)/$(@F)
	mv $@.tmp $@

$(BUILD_DIR)/docker-mirror/build.done: \
		$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_IMAGE_FILES))
	mkdir -p $(@D)
	touch $@

.PHONY: clean-docker

clean: clean-docker

clean-docker:
	-sudo sh -c "docker ps -aq | xargs --no-run-if-empty docker rm -f"
	-sudo sh -c "docker images | awk '/fuel|none/ { print \$$3; }' | xargs --no-run-if-empty docker rmi -f"


