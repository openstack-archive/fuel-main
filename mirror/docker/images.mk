DOCKER_IMAGES:=storage-dump.tar.xz storage-puppet.tar.xz storage-repo.tar.xz cobbler.tar.xz nailgun.tar.xz nginx.tar.xz dump.tar.xz repo.tar.xz puppet.tar.xz ostf.tar.xz postgres.tar.xz rabbitmq.tar.xz rsyslog.tar.xz mcollective.tar.xz

# Fuel node docker images
$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(DOCKER_IMAGES)):
	@mkdir -p $(@D)
	wget -O $@ $(MIRROR_DOCKER_BASEURL)/$(@F)

ifeq ($(DOCKER_REBUILD),true)
include $(SOURCE_DIR)/docker/cobbler/build.mk
#include $(SOURCE_DIR)/docker/nailgun/build.mk
#include $(SOURCE_DIR)/docker/nginx/build.mk
#include $(SOURCE_DIR)/docker/dump/build.mk
#include $(SOURCE_DIR)/docker/repo/build.mk
#include $(SOURCE_DIR)/docker/puppet/build.mk
#include $(SOURCE_DIR)/docker/postgres/build.mk
#include $(SOURCE_DIR)/docker/rabbitmq/build.mk
#include $(SOURCE_DIR)/docker/rsyslog/build.mk
#include $(SOURCE_DIR)/docker/mcollective/build.mk
$(BUILD_DIR)/mirror/docker/images.done: \
	$(BUILD_DIR)/mirror/docker/cobbler.done 
	$(ACTION.TOUCH)
else
$(BUILD_DIR)/mirror/docker/images.done: \
		$(addprefix $(LOCAL_MIRROR_DOCKER_BASEURL)/,$(DOCKER_IMAGES)) \
	$(ACTION.TOUCH)
endif
