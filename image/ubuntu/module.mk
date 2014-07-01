.PHONY: target_ubuntu_image

target_ubuntu_image: $(ARTS_DIR)/$(TARGET_UBUNTU_IMG_ART_NAME)

$(ARTS_DIR)/$(TARGET_UBUNTU_IMG_ART_NAME): $(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME)
	$(ACTION.COPY)

TARGET_UBUNTU_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(TARGET_UBUNTU_IMG_ART_NAME))

ifdef TARGET_UBUNTU_DEP_FILE
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): $(TARGET_UBUNTU_DEP_FILE)
	$(ACTION.COPY)
else
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): $(BUILD_DIR)/mirror/build.done
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME):
	@mkdir -p $(@D)
	mkdir -p $(BUILD_DIR)/image/ubuntu
	truncate -s 1G $(BUILD_DIR)/image/ubuntu/ubuntu_$(UBUNTU_IMAGE_RELEASE)_$(UBUNTU_ARCH).img
	mkfs.ext4 -F $(BUILD_DIR)/image/ubuntu/ubuntu_$(UBUNTU_IMAGE_RELEASE)_$(UBUNTU_ARCH).img
	mkdir $(BUILD_DIR)/image/ubuntu/mnt
	sudo mount $(BUILD_DIR)/image/ubuntu/ubuntu_$(UBUNTU_IMAGE_RELEASE)_$(UBUNTU_ARCH).img $(BUILD_DIR)/image/ubuntu/mnt -o loop
# FIXME(kozhukalov): remove particular kernel version
	sudo debootstrap --no-check-gpg --arch=$(UBUNTU_ARCH) --include=sudo,adduser,locales,openssh-server,file,less,kbd,curl,rsync,bash-completion,ubuntu-minimal,linux-image-$(UBUNTU_INSTALLER_KERNEL_VERSION)-generic,linux-headers-$(UBUNTU_INSTALLER_KERNEL_VERSION),util-linux,ntp,ntpdate,virt-what,grub-pc-bin,grub-pc,cloud-init $(UBUNTU_RELEASE) $(BUILD_DIR)/image/ubuntu/mnt file://$(LOCAL_MIRROR)/ubuntu
#	sudo rm -fr $(BUILD_DIR)/image/ubuntu/mnt/boot
	sudo umount -f $(BUILD_DIR)/image/ubuntu/ubuntu_$(UBUNTU_IMAGE_RELEASE)_$(UBUNTU_ARCH).img
	gzip -f $(BUILD_DIR)/image/ubuntu/ubuntu_$(UBUNTU_IMAGE_RELEASE)_$(UBUNTU_ARCH).img
	rm -fr $(BUILD_DIR)/image/ubuntu/mnt
	tar cf $@ -C $(BUILD_DIR)/image ubuntu
endif
