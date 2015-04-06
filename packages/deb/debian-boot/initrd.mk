NETBOOT_PATH=$(LOCAL_MIRROR)/ubuntu/installer-amd64/current/images/netboot/ubuntu-installer/amd64

# script which mounts /proc in /target. linux-image* preinst script uses
# /proc without checking if its mounted, hence this work around:
hook_script:=$(SOURCE_DIR)/packages/deb/debian-boot/01_mount_target_proc.sh
# Debian installer runs scripts located in this directory before installing
# the kernel (and after the base has been installed)
hook_target_dir:=/usr/lib/post-base-installer.d

$(BUILD_DIR)/packages/deb/debian-boot/initrd.done:\
		$(BUILD_DIR)/mirror/ubuntu/boot.done
	mkdir -p $(@D)
	mkdir -p $(@D)-orig
	cd $(@D)-orig && gunzip -c $(NETBOOT_PATH)/initrd.gz | sudo cpio -di
	cd $(@D)-orig && sudo patch -p1 < $(SOURCE_DIR)/packages/deb/debian-boot/preseed-retry.patch
	# copy helper script into a directory where the installer expects to find it
	sudo mkdir -p $(@D)-orig$(hook_target_dir)
	sudo cp $(hook_script) $(@D)-orig$(hook_target_dir) 
	cd $(@D)-orig && sudo find . | sudo cpio --create --format='newc' > $(BUILD_DIR)/packages/deb/debian-boot/initrd.gz
	$(ACTION.TOUCH)
