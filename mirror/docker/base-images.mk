BASE_IMAGE_FILES:=centos.tar.xz busybox.tar.xz nsenter.tar.xz

# docker base image files
$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_IMAGE_FILES)):
	@mkdir -p $(@D)
	#Fix ugly hack and get centos.tar.xz in mirror
	wget -nv -O $@ $(MIRROR_DOCKER_BASEURL)/$(@F) || wget -nv -O https://github.com/CentOS/sig-cloud-instance-images/blob/684a5ab43827c8316810e5d2abe6ce60e2d68e6e/docker/centos-6-20150102_1408-docker.tar.xz

$(BUILD_DIR)/mirror/docker/base-images.done: \
		$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_IMAGE_FILES))
	$(ACTION.TOUCH)
