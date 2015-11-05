$(BUILD_DIR)/mirror/centos/mos-download.done: $(BUILD_DIR)/mirror/centos/yum-config.done
	mkdir -p $(@D)
	mkdir -p $(LOCAL_MIRROR_MOS_CENTOS)
	set -ex ; reposync --norepopath --downloadcomps --plugins --delete --arch=$(CENTOS_ARCH) \
	    -c $(BUILD_DIR)/mirror/centos/etc/yum.conf --repoid=fuel -p $(LOCAL_MIRROR_MOS_CENTOS)
	$(ACTION.TOUCH)

$(BUILD_DIR)/mirror/centos/mos-repo.done: $(BUILD_DIR)/mirror/centos/mos-download.done
	createrepo -g $(LOCAL_MIRROR_MOS_CENTOS)/comps.xml \
	    -u media://`head -1 $(SOURCE_DIR)/iso/.discinfo` \
	    -o $(LOCAL_MIRROR_MOS_CENTOS)/ $(LOCAL_MIRROR_MOS_CENTOS)/
	$(ACTION.TOUCH)

