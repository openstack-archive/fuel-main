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
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): $(call find-files,$(BUILD_DIR)/image/ubuntu/$(TARGET_UBUNTU_IMG_ART_NAME))
	@mkdir -p $(@D)
	echo $(@D)
	truncate -s 1G $(BUILD_DIR)/image/ubuntu/ubuntu.img
	mkfs.ext4 -F $(BUILD_DIR)/image/ubuntu/ubuntu.img
	mkdir $(BUILD_DIR)/image/ubuntu/mnt
	sudo mount $(BUILD_DIR)/image/ubuntu/ubuntu.img $(BUILD_DIR)/image/ubuntu/mnt -o loop
# FIXME(kozhukalov): remove particular kernel version
	sudo debootstrap --no-check-gpg --arch=amd64 --include=sudo,adduser,locales,openssh-server,file,less,kbd,curl,rsync,bash-completion,ubuntu-minimal,linux-image-3.11.0-18-generic,linux-headers-3.11.0-18,util-linux,ntp,ntpdate,virt-what,grub-pc-bin,grub-pc,cloud-init precise $(BUILD_DIR)/image/ubuntu/mnt file://$(LOCAL_MIRROR)/ubuntu
	sudo find $(BUILD_DIR)/image/ubuntu/mnt/boot -iname 'initrd*' -exec sudo chmod a+r '{}' \; -exec cp -f '{}' $(BUILD_DIR)/image/ubuntu \;
	sudo find $(BUILD_DIR)/image/ubuntu/mnt/boot -iname 'vmlinuz*' -exec sudo chmod a+r '{}' \; -exec cp -f '{}' $(BUILD_DIR)/image/ubuntu \;
#	sudo rm -fr $(BUILD_DIR)/image/ubuntu/mnt/boot
	sudo umount -f $(BUILD_DIR)/image/ubuntu/ubuntu.img
	gzip -f $(BUILD_DIR)/image/ubuntu/ubuntu.img
	rm -fr $(BUILD_DIR)/image/ubuntu/mnt
	tar czf $@ -C $(BUILD_DIR)/image ubuntu
endif
