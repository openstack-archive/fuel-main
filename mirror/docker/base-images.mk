BASE_IMAGE_FILES:=fuel-centos.tar.xz busybox.tar.xz nsenter.tar.xz
BASE_UPSTREAM_IMAGE_FILES:=busybox.tar.xz centos-centos6.tar.xz

# docker base image files
$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_IMAGE_FILES)):
	@mkdir -p $(@D)
	wget -nv -O $@ $(MIRROR_DOCKER_BASEURL)/$(@F)

# docker base image files from upstream
ifeq ($(USE_MIRROR),none)
$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_UPSTREAM_IMAGE_FILES)):
	@mkdir -p $(@D)
	sudo docker pull $(subst -,:,$(subst .tar.xz,,$(@F)))
	sudo docker save $(subst -,:,$(subst .tar.xz,,$(@F))) | xz -c -T0 -4 > $(LOCAL_MIRROR_DOCKER_BASEURL)/$(@F)
endif

ifeq ($(USE_MIRROR),none)
$(BUILD_DIR)/mirror/docker/base-images.done: \
		$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_UPSTREAM_IMAGE_FILES)) \
		$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_IMAGE_FILES))
else
$(BUILD_DIR)/mirror/docker/base-images.done: \
		$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(BASE_IMAGE_FILES))
endif

$(BUILD_DIR)/mirror/docker/base-images.done:
	$(ACTION.TOUCH)