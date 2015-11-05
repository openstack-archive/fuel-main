$(BUILD_DIR)/mirror/centos/mos-repo.done:
	mkdir -p $(@D)
	mkdir -p $(LOCAL_MIRROR_MOS_CENTOS)/os
	set -ex; cd $(LOCAL_MIRROR_MOS_CENTOS)/os ; \
	wget --no-verbose --no-host-directories --cut-dirs=4 --recursive --no-parent --relative --reject '*debuginfo*,*.html' \
	--exclude-directories='/mos-repos/centos/$(PRODUCT_NAME)$(PRODUCT_VERSION)-centos$(CENTOS_MAJOR)-fuel/os/Source' \
	$(MIRROR_MOS_CENTOS_METHOD)://$(MIRROR_MOS_CENTOS)$(MIRROR_MOS_CENTOS_ROOT)
	$(ACTION.TOUCH)
