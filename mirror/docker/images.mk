DOCKER_IMAGES:=storage-dump.tar.xz storage-puppet.tar.xz storage-repo.tar.xz cobbler.tar.xz nailgun.tar.xz nginx.tar.xz dump.tar.xz repo.tar.xz puppet.tar.xz ostf.tar.xz postgres.tar.xz rabbitmq.tar.xz rsyslog.tar.xz mcollective.tar.xz

# Fuel node docker images
$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/docker/,$(DOCKER_IMAGES)):
	@mkdir -p $(@D)
	wget -O $@ $(MIRROR_DOCKER_BASEURL)/$(@F)

$(BUILD_DIR)/mirror/docker/images.done: \
		$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/docker/,$(DOCKER_IMAGES)) \
	$(ACTION.TOUCH)
