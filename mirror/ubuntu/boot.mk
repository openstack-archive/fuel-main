ISOLINUX_FILES:=netboot.tar.gz

LOCAL_NETBOOT_DIR:=$(LOCAL_MIRROR_UBUNTU_OS_BASEURL)/installer-amd64/current/images/netboot
LOCAL_NETBOOT_TGZ:=$(LOCAL_NETBOOT_DIR)/$(ISOLINUX_FILES)
NETBOOT_URL:=$(MIRROR_UBUNTU)/installer-amd64/current/images/netboot/netboot.tar.gz
ifeq ($(USE_MIRROR),none)
	NETBOOT_URL:=$(MIRROR_UBUNTU)/ubuntu/dists/$(UBUNTU_RELEASE)-updates/main/installer-amd64/current/images/$(UBUNTU_NETBOOT_FLAVOR)/netboot.tar.gz
endif

patched_di_initrd_img:=$(LOCAL_NETBOOT_DIR)/ubuntu-installer/amd64/initrd.gz
di_initrd_img:=$(patched_di_initrd_img).orig

# download the Debian installer netboot
$(LOCAL_NETBOOT_TGZ):
	@mkdir -p $(@D)
	wget -nv -O $@.tmp $(NETBOOT_URL)
	mv $@.tmp $@

$(di_initrd_img): tmpdir=$(LOCAL_NETBOOT_DIR)_tmp

# extract the kernel and initrd from the netboot
$(di_initrd_img): $(LOCAL_NETBOOT_TGZ)
	mkdir -p $(tmpdir)
	tar -xzf $< -C $(tmpdir)
	cd $(tmpdir)/ubuntu-installer/amd64; mv initrd.gz initrd.gz.orig
	rsync -avH $(tmpdir)/ $(LOCAL_NETBOOT_DIR)/
	-rm -rf $(tmpdir)

$(patched_di_initrd_img): initrd_dir=$(dir $(patched_di_initrd_img))initrd_dir
# script which mounts /proc in /target. linux-image* preinst script uses
# /proc without checking if its mounted, hence this work around:
$(patched_di_initrd_img): hook_script:=$(SOURCE_DIR)/mirror/ubuntu/boot/01_mount_target_proc.sh
# Debian installer runs scripts located in this directory before installing
# the kernel (and after the base has been installed)
$(patched_di_initrd_img): hook_target_dir:=/usr/lib/post-base-installer.d

# unpack the initrd, apply patches, and repack it
$(patched_di_initrd_img): $(di_initrd_img)
	mkdir -p $(initrd_dir)
	set -e; cd $(initrd_dir); \
	zcat $< | sudo cpio -di; \
	sudo chown -R `whoami` .; \
	patch -p1 < $(SOURCE_DIR)/mirror/ubuntu/boot/preseed-retry.patch; \
	mkdir -p .$(hook_target_dir); \
	cp $(hook_script) .$(hook_target_dir); \
	find . | cpio --create --format='newc' --owner=root:root | gzip -9 > $@.tmp
	mv $@.tmp $@
	-rm -rf $(initrd_dir)

$(BUILD_DIR)/mirror/ubuntu/boot.done: $(patched_di_initrd_img)
	$(ACTION.TOUCH)

di_kernel_modules_dir=$(shell zcat $(di_initrd_img) | cpio --list 'lib/modules/*/kernel')
UBUNTU_INSTALLER_KERNEL_VERSION=$(strip $(patsubst lib/modules/%/kernel,%,$(di_kernel_modules_dir)))

$(BUILD_DIR)/ubuntu_installer_kernel_version.mk: $(di_initrd_img)
	echo 'UBUNTU_INSTALLER_KERNEL_VERSION:=$(UBUNTU_INSTALLER_KERNEL_VERSION)' > $@


