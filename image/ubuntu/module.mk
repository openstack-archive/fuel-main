.PHONY: target_ubuntu_image

target_ubuntu_image: $(ARTS_DIR)/$(TARGET_UBUNTU_IMG_ART_NAME)

$(ARTS_DIR)/$(TARGET_UBUNTU_IMG_ART_NAME): $(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME)
	$(ACTION.COPY)

TARGET_UBUNTU_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(TARGET_UBUNTU_IMG_ART_NAME))

#PKGS_INCLUDE:=sudo,adduser,locales,openssh-server,file,less,kbd,curl,rsync,bash-completion,ubuntu-minimal,linux-image-$(UBUNTU_INSTALLER_KERNEL_VERSION)-generic,linux-headers-$(UBUNTU_INSTALLER_KERNEL_VERSION),util-linux,ntp,ntpdate,virt-what,grub-pc-bin,grub-pc,cloud-init,lvm2,mdadm
PKGS_INCLUDE:=sudo,adduser,locales,openssh-server,file,less,kbd,curl,rsync,bash-completion,ubuntu-minimal,linux-image-$(UBUNTU_INSTALLER_KERNEL_VERSION)-generic,linux-headers-$(UBUNTU_INSTALLER_KERNEL_VERSION),util-linux,ntp,ntpdate,virt-what,grub-pc-bin,grub-pc,cloud-init
TMP_CHROOT:=$(BUILD_DIR)/image/tmp/ubuntu_chroot
SEPARATE_IMAGES:=/boot,ext2 /,ext4 /var,ext3

ifdef TARGET_UBUNTU_DEP_FILE
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): $(TARGET_UBUNTU_DEP_FILE)
	$(ACTION.COPY)
else
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): $(BUILD_DIR)/mirror/build.done
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): export SEPARATE_FS_IMAGES=$(SEPARATE_IMAGES)
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): export TMP_BUILD_DIR=$(BUILD_DIR)/image/tmp
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): export TMP_BUILD_IMG_DIR=$(BUILD_DIR)/image/ubuntu
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): export TMP_CHROOT_DIR=$(TMP_CHROOT)
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): export IMG_SUFFIX=$(UBUNTU_IMAGE_RELEASE)_$(UBUNTU_ARCH)
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): export DEBOOTSRAP_PARAMS=--no-check-gpg --arch=$(UBUNTU_ARCH) --include=$(PKGS_INCLUDE) $(UBUNTU_RELEASE) $(TMP_CHROOT) file://$(LOCAL_MIRROR)/ubuntu
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME):
	@mkdir -p $(@D)
	mkdir -p $(BUILD_DIR)/image/ubuntu
	touch $(BUILD_DIR)/image/ubuntu/profile.yaml
	bash ./image/ubuntu/create_separate_images.sh
	find $(BUILD_DIR)/image/ubuntu -name '*img' -exec gzip -f {} \;
	tar cf $@ -C $(BUILD_DIR)/image/ubuntu .
endif
