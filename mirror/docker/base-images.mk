BASE_IMAGE_FILES:=centos.tar.xz busybox.tar.xz

# docker base image files
$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_IMAGE_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@ $(MIRROR_DOCKER)/$(@F)

$(BUILD_DIR)/mirror/docker/base-images.done: \
		$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_IMAGE_FILES))
	$(ACTION.TOUCH)
