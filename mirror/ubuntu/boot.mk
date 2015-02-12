ISOLINUX_FILES:=netboot.tar.gz

LOCAL_NETBOOT_DIR:=$(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/installer-amd64/current/images/netboot
LOCAL_NETBOOT_TGZ:=$(LOCAL_NETBOOT_DIR)/$(ISOLINUX_FILES)
#NETBOOT_URL:=$(MIRROR_UBUNTU)/installer-amd64/current/images/netboot/netboot.tar.gz
NETBOOT_URL:=http://cz.archive.ubuntu.com/ubuntu/dists/trusty-updates/main/installer-amd64/20101020ubuntu318.15/images/netboot/netboot.tar.gz
#http://cz.archive.ubuntu.com/ubuntu/dists/precise-updates/main/installer-amd64/current/images/trusty-netboot/netboot.tar.gz
#ifeq ($(USE_MIRROR),none)
#	NETBOOT_URL:=$(MIRROR_UBUNTU)/ubuntu/dists/$(UBUNTU_RELEASE)-updates/main/installer-amd64/current/images/$(UBUNTU_NETBOOT_FLAVOR)/netboot.tar.gz
#endif

# debian isolinux files
$(LOCAL_NETBOOT_TGZ):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(NETBOOT_URL)
	mv $@.tmp $@
	tar -xzf $@ -C $(@D)

$(BUILD_DIR)/mirror/ubuntu/boot.done: $(LOCAL_NETBOOT_TGZ)
	$(ACTION.TOUCH)

di_initrd_img:=$(LOCAL_NETBOOT_DIR)/ubuntu-installer/amd64/initrd.gz
di_kernel_modules_dir=$(shell zcat $(di_initrd_img) | cpio --list 'lib/modules/*/kernel')
UBUNTU_INSTALLER_KERNEL_VERSION=$(strip $(patsubst lib/modules/%/kernel,%,$(di_kernel_modules_dir)))

$(BUILD_DIR)/ubuntu_installer_kernel_version.mk: $(LOCAL_NETBOOT_TGZ)
	echo 'UBUNTU_INSTALLER_KERNEL_VERSION:=$(UBUNTU_INSTALLER_KERNEL_VERSION)' > $@
