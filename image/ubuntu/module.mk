.PHONY: target_ubuntu_image clean_ubuntu_image clean

target_ubuntu_image: $(ARTS_DIR)/$(TARGET_UBUNTU_IMG_ART_NAME)

clean: clean_ubuntu_image

clean_ubuntu_image:
	-sudo umount $(TMP_CHROOT)/proc
	-sudo umount $(TMP_CHROOT)/dev
	-sudo umount $(TMP_CHROOT)/sys
	-sudo umount $(TMP_CHROOT)/boot
	-sudo umount $(TMP_CHROOT)
	sudo rm -rf $(TMP_CHROOT)
	sudo rm -rf $(BUILD_DIR)/image/ubuntu
	sudo rm -f $(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME)
	sudo rm -f $(ARTS_DIR)/$(TARGET_UBUNTU_IMG_ART_NAME)

$(ARTS_DIR)/$(TARGET_UBUNTU_IMG_ART_NAME): $(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME)
	$(ACTION.COPY)

TARGET_UBUNTU_DEP_FILE:=$(call find-files,$(DEPS_DIR_CURRENT)/$(TARGET_UBUNTU_IMG_ART_NAME))

#NOTE: ubuntu-minimal package depends on: adduser apt apt-utils bzip2 console-setup
#      debconf debconf-i18n eject gnupg ifupdown initramfs-tools iproute iputils-ping
#      isc-dhcp-client kbd less locales lsb-release makedev mawk module-init-tools
#      net-tools netbase netcat-openbsd ntpdate passwd procps python resolvconf
#      rsyslog sudo tzdata ubuntu-keyring udev upstart ureadahead vim-tiny whiptail

comma:=,
space:=
space+=
PKGS_INCLUDE:=\
bash-completion\
bind9-host\
cron\
curl\
daemonize\
dnsutils\
file\
gcc\
gdisk\
grub-pc\
grub-pc-bin\
iptables\
linux-firmware\
linux-firmware-nonfree\
linux-headers-$(UBUNTU_INSTALLER_KERNEL_VERSION)\
linux-image-$(UBUNTU_INSTALLER_KERNEL_VERSION)-generic\
lvm2\
make\
mdadm\
mlocate\
nailgun-agent\
nailgun-mcagents\
nailgun-net-check\
ntp\
openssh-client\
openssh-server\
perl\
rsync\
telnet\
ubuntu-minimal\
util-linux\
virt-what\
wget

PKGS_APTGET:=\
acl\
anacron\
cloud-init\
debconf-utils\
libaugeas-ruby\
libstomp-ruby1.8\
libshadow-ruby1.8\
libjson-ruby1.8\
mcollective\
mlnx-ofed-light\
puppet\
python-amqp\
ruby-ipaddress\
ruby-netaddr\
ruby-openstack\
ruby-stomp\
vim\
vlan\
uuid-runtime

TMP_CHROOT:=$(BUILD_DIR)/image/tmp/ubuntu_chroot

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
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): export DEBOOTSTRAP_PARAMS=--no-check-gpg --arch=$(UBUNTU_ARCH) --include=$(subst $(space),$(comma),$(PKGS_INCLUDE)) $(UBUNTU_RELEASE) $(TMP_CHROOT) file://$(LOCAL_MIRROR)/ubuntu
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME): export INSTALL_PACKAGES=$(PKGS_APTGET)
$(BUILD_DIR)/images/$(TARGET_UBUNTU_IMG_ART_NAME):
	@mkdir -p $(@D)
	mkdir -p $(BUILD_DIR)/image/ubuntu
	touch $(BUILD_DIR)/image/ubuntu/profile.yaml
	env LOCAL_MIRROR=$(LOCAL_MIRROR) \
	    UBUNTU_MAJOR=$(UBUNTU_MAJOR) \
	    UBUNTU_MINOR=$(UBUNTU_MINOR) \
	    UBUNTU_ARCH=$(UBUNTU_ARCH) \
	    $(SOURCE_DIR)/image/ubuntu/create_separate_images.sh
	find $(BUILD_DIR)/image/ubuntu -name '*img' -exec gzip -f {} \;
	tar cf $@ -C $(BUILD_DIR)/image/ubuntu .
endif
