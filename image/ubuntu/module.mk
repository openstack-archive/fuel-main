.PHONY: target_ubuntu_image

target_ubuntu_image: $(ARTS_DIR)/$(TARGET_UBUNTU_IMG_ART_NAME)

$(ARTS_DIR)/$(TARGET_UBUNTU_IMG_ART_NAME): $(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME)
	$(ACTION.COPY)

TARGET_UBUNTU_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(TARGET_UBUNTU_IMG_ART_NAME))

#NOTE: ubuntu-minimal package depends on: adduser apt apt-utils bzip2 console-setup
#      debconf debconf-i18n eject gnupg ifupdown initramfs-tools iproute iputils-ping
#      isc-dhcp-client kbd less locales lsb-release makedev mawk module-init-tools
#      net-tools netbase netcat-openbsd ntpdate passwd procps python resolvconf
#      rsyslog sudo tzdata ubuntu-keyring udev upstart ureadahead vim-tiny whiptail

space:=
space+=
PKGS_INCLUDE:=\
bash-completion,\
bind9-host,\
cloud-init,\
cron,\
curl,\
daemonize,\
dnsutils,\
file,\
gcc,\
gdisk,\
grub-pc,\
grub-pc-bin,\
linux-firmware,\
linux-firmware-nonfree,\
linux-headers-$(UBUNTU_INSTALLER_KERNEL_VERSION),\
linux-image-$(UBUNTU_INSTALLER_KERNEL_VERSION)-generic,\
lvm2,\
make,\
mdadm,\
mlocate,\
nailgun-net-check,\
ntp,\
openssh-client,\
openssh-server,\
perl,\
rsync,\
telnet,\
ubuntu-minimal,\
util-linux,\
virt-what,\
wget

TMP_CHROOT:=$(BUILD_DIR)/image/tmp/ubuntu_chroot
#TODO(agordeev): allow to specify SEPARATE_IMAGES during build, don't hardcode it
SEPARATE_IMAGES:=/boot,ext4 /,ext4

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
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): export DEBOOTSRAP_PARAMS=--no-check-gpg --arch=$(UBUNTU_ARCH) --include=$(subst $(space),,$(PKGS_INCLUDE)) $(UBUNTU_RELEASE) $(TMP_CHROOT) file://$(LOCAL_MIRROR)/ubuntu
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME):
	@mkdir -p $(@D)
	mkdir -p $(BUILD_DIR)/image/ubuntu
	touch $(BUILD_DIR)/image/ubuntu/profile.yaml
	bash ./image/ubuntu/create_separate_images.sh
	find $(BUILD_DIR)/image/ubuntu -name '*img' -exec gzip -f {} \;
	tar cf $@ -C $(BUILD_DIR)/image/ubuntu .
endif
