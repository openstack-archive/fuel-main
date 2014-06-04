BASE_IMAGE_FILES:=centos-fuel.tar.xz busybox.tar.xz

# docker base image files
$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_IMAGE_FILES)):
	@mkdir -p $(@D)
	wget -O $@ $(MIRROR_DOCKER_BASEURL)/$(@F)

$(BUILD_DIR)/mirror/docker/base-images.done: \
		$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_IMAGE_FILES))
	$(ACTION.TOUCH)
