.PHONY: target_centos_image clean clean_centos_image

target_centos_image: $(ARTS_DIR)/$(TARGET_CENTOS_IMG_ART_NAME)

clean: clean_centos_image

clean_centos_image:
	-sudo umount $(BUILD_DIR)/image/centos/SANDBOX/mirror
	-sudo umount $(BUILD_DIR)/image/centos/SANDBOX/proc
	-sudo umount $(BUILD_DIR)/image/centos/SANDBOX/dev
	-mount | grep '$(BUILD_DIR)/image/centos/SANDBOX' | sort -r | \
		while read entry; do \
			set -- $$entry; \
			mntpt="$$3"; \
			sudo umount $$mntpt; \
		done
	sudo rm -rf $(BUILD_DIR)/image/centos

$(ARTS_DIR)/$(TARGET_CENTOS_IMG_ART_NAME): $(BUILD_DIR)/images/$(TARGET_CENTOS_IMG_ART_NAME)
	$(ACTION.COPY)

TARGET_CENTOS_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(TARGET_CENTOS_IMG_ART_NAME))

ifdef TARGET_CENTOS_DEP_FILE
$(BUILD_DIR)/images/$(TARGET_CENTOS_IMG_ART_NAME): $(TARGET_CENTOS_DEP_FILE)
	$(ACTION.COPY)
else
$(BUILD_DIR)/images/$(TARGET_CENTOS_IMG_ART_NAME): $(BUILD_DIR)/mirror/centos/build.done
$(BUILD_DIR)/images/$(TARGET_CENTOS_IMG_ART_NAME): $(BUILD_DIR)/packages/rpm/build.done
$(BUILD_DIR)/images/$(TARGET_CENTOS_IMG_ART_NAME): SANDBOX:=$(BUILD_DIR)/image/centos/SANDBOX
$(BUILD_DIR)/images/$(TARGET_CENTOS_IMG_ART_NAME): export SANDBOX_UP:=$(SANDBOX_UP)
$(BUILD_DIR)/images/$(TARGET_CENTOS_IMG_ART_NAME): export SANDBOX_DOWN:=$(SANDBOX_DOWN)
$(BUILD_DIR)/images/$(TARGET_CENTOS_IMG_ART_NAME):
	@mkdir -p $(@D)
	mkdir -p $(BUILD_DIR)/image/centos
	sudo sh -c "$${SANDBOX_UP}"
	sudo yum -c $(SANDBOX)/etc/yum.conf --installroot=$(SANDBOX) -y --nogpgcheck install tar python-setuptools git python-imgcreate python-argparse PyYAML
	sudo cp /etc/mtab $(SANDBOX)/etc/mtab
	sudo mkdir -p $(SANDBOX)/run/shm
	sudo cp $(SOURCE_DIR)/image/centos/build_centos_image.py $(SANDBOX)/build_centos_image.py
	sudo cp $(SOURCE_DIR)/image/centos/centos.ks $(SANDBOX)/centos.ks
	sudo mkdir -p $(SANDBOX)/mirror
	sudo mount -o bind $(LOCAL_MIRROR_CENTOS_OS_BASEURL) $(SANDBOX)/mirror
	sudo chroot $(SANDBOX) python build_centos_image.py -k centos.ks -n centos_$(CENTOS_IMAGE_RELEASE)_$(CENTOS_ARCH) -s "$(SEPARATE_IMAGES)" -O centos_$(CENTOS_IMAGE_RELEASE)_$(CENTOS_ARCH).yaml
	sudo umount $(SANDBOX)/mirror
	sudo mv $(SANDBOX)/centos_$(CENTOS_IMAGE_RELEASE)_$(CENTOS_ARCH)* $(BUILD_DIR)/image/centos/
	gzip -f $(BUILD_DIR)/image/centos/centos_$(CENTOS_IMAGE_RELEASE)_$(CENTOS_ARCH)*.img
	sudo sh -c "$${SANDBOX_DOWN}"
	tar cf $@.tmp $(BUILD_DIR)/image/centos/centos_$(CENTOS_IMAGE_RELEASE)_$(CENTOS_ARCH)* --xform s:^:/: --xform s:$(BUILD_DIR)/image/centos/::
	mv $@.tmp $@
endif
